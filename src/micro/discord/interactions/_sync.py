"""Command sync: registers converged command definitions with Discord."""

import asyncio
import hashlib
import json
import logging
from typing import Any, cast

from pydantic import BaseModel, ConfigDict, JsonValue

from micro import subjects
from micro.coordination import Declarations
from micro.errors import MicroError
from micro.runtime import Component, default_backoff

from ._runtime_commands import PREFIX, _Stored, runtime_definitions

logger = logging.getLogger("micro")

SYNC_LOCK = "commands.sync"
SYNCED_PREFIX = "synced.commands."
ENTRY_POINT = 4
"""An Activity's entry-point command: Discord manages it, so comparisons skip it."""


class SyncFailed(MicroError, RuntimeError):
  """Some scopes could not be updated; every other scope was."""

  def __init__(self, failures: dict[str, Exception]) -> None:
    self.failures = failures
    super().__init__(
      "; ".join(f"{scope}: {error}" for scope, error in sorted(failures.items()))
    )


class _Synced(BaseModel):
  model_config = ConfigDict(extra="ignore")

  hash: str


class CommandSync(Component):
  """Keeps Discord's application commands equal to the converged declarations.

  Every service declares its commands; this component registers a definition
  only when every live replica declaring it agrees, so a rolling update or a
  rollback never registers a half-deployed version, and a service restarting
  never unregisters anything (`micro commands forget` retires a command).
  Each scope (global and every guild) is bulk-overwritten only when its hash
  changes, under a cluster lock, so running several replicas is safe. Scopes are
  independent: one Discord refuses (a guild the bot left) is retried and
  reported without holding up the others. The first pass after starting also
  compares each scope with what Discord has, so commands removed or edited
  elsewhere are repaired.
  """

  kind = "command-sync"

  def __init__(self, name: str = "command-sync") -> None:
    super().__init__(name)
    self._changed = asyncio.Event()
    self.synced = asyncio.Event()
    """Set after each successful pass."""
    self._application_id: str | None = None
    self._verified = False

  async def on_start(self) -> None:
    """Begin watching declarations and runtime commands, and run the sync loop."""
    declarations = Declarations(self.runtime, "commands")
    self._unwatch = self.runtime.directory.on_change(
      self._changed.set, watching=declarations.live
    )
    self._changed.set()
    self.spawn(self._loop(), name="sync")
    self.spawn(self._watch_runtime_commands(), name="runtime-commands")

  async def _watch_runtime_commands(self) -> None:
    """Sync again whenever a runtime command is added, changed, or removed."""
    table = await self.runtime.table(subjects.STATE_BUCKET, _Stored)
    failures = 0
    while True:
      caught_up = False
      try:
        async for change in table.watch(PREFIX + ">", lenient=True):
          failures = 0
          if change is None:
            caught_up = True
          elif caught_up:
            self._changed.set()
      except asyncio.CancelledError:
        raise
      except Exception:
        logger.warning("The watch on runtime commands failed", exc_info=True)
      failures += 1
      await asyncio.sleep(default_backoff(failures))
      self._changed.set()  # whatever changed meanwhile is picked up by a pass

  async def on_close(self) -> None:
    """Stop watching."""
    self._unwatch()

  async def _loop(self) -> None:
    delay = 0.5
    reported: str | None = None
    while self.active:
      await self._changed.wait()
      self._changed.clear()
      try:
        await self.sync()
        if reported is not None:
          logger.info("Command sync recovered")
          reported = None
        delay = 0.5
      except asyncio.CancelledError:
        raise
      except Exception as exc:
        message = str(exc)
        if message != reported:
          level = logging.WARNING if isinstance(exc, SyncFailed) else logging.INFO
          logger.log(level, "Command sync will retry: %s", message)
          reported = message
        else:
          logger.debug("Command sync is still failing: %s", message)
        await asyncio.sleep(delay)
        delay = min(delay * 2, 30.0)
        self._changed.set()

  async def sync(self, *, verify: bool = False) -> bool:
    """One pass; returns True if Discord's commands changed.

    `verify` also compares scopes that look up to date with what Discord has.
    """
    from micro.discord import DiscordHTTPClient

    http = DiscordHTTPClient(self.runtime)
    if self._application_id is None:
      self._application_id = str((await http.call("get_my_application"))["id"])
    locks = await self.runtime.locks()
    async with locks.hold(SYNC_LOCK, ttl=30):
      try:
        changed = await sync_commands(
          self.runtime,
          http,
          self._application_id,
          verify=verify or not self._verified,
        )
      except SyncFailed:
        self._verified = True  # the scopes that worked were compared with Discord
        raise
    self._verified = True
    self.synced.set()
    return changed


async def sync_commands(
  runtime: Any, http: Any, application_id: str, *, verify: bool = False
) -> bool:
  """Bulk-overwrite every scope whose converged commands changed (hold SYNC_LOCK).

  Scopes are independent, global first: one that fails is collected into a
  `SyncFailed` raised after the others were done, and a command is marked
  applied only if every scope it belongs to succeeded. With `verify`, a scope
  that looks up to date is also compared with Discord's own list.
  """
  declarations = Declarations(runtime, "commands")
  view = await declarations.view()
  scopes: dict[str, dict[str, JsonValue]] = {}
  scopes_of: dict[str, list[str]] = {}
  for key, declared in view.items():
    definition = dict(cast(dict[str, Any], declared.document))
    guilds = definition.pop("guild_ids", None) or []
    for scope in [str(guild) for guild in guilds] if guilds else ["global"]:
      scopes.setdefault(scope, {})[key] = definition
      scopes_of.setdefault(key, []).append(scope)
  for key, definition in (await runtime_definitions(runtime)).items():
    guilds = cast(list[Any], definition.pop("guild_ids", None) or [])
    base = key.partition("#")[0]
    if base in view:
      logger.warning("Runtime command %s is also declared in code; using that", base)
      continue
    for scope in [str(guild) for guild in guilds] if guilds else ["global"]:
      scopes.setdefault(scope, {}).setdefault(base, definition)
      scopes_of.setdefault(key, []).append(scope)
  synced = await runtime.table(subjects.STATE_BUCKET, _Synced)
  previous = {
    key.removeprefix(SYNCED_PREFIX): entry.value.hash
    for key, entry in (await synced.items(SYNCED_PREFIX + ">")).items()
  }
  changed = False
  failed: dict[str, Exception] = {}
  for scope in sorted(
    set(scopes) | set(previous), key=lambda item: (item != "global", item)
  ):
    commands: list[JsonValue] = [
      scopes.get(scope, {})[key] for key in sorted(scopes.get(scope, {}))
    ]
    digest = hashlib.sha256(
      json.dumps(commands, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    try:
      if previous.get(scope) == digest and not (
        verify and await _drifted(http, application_id, scope, commands)
      ):
        continue
      await _overwrite(http, application_id, scope, commands)
    except Exception as error:
      if not commands and _unreachable(error):
        # Nothing to clear in a guild the bot is no longer in.
        await synced.delete(SYNCED_PREFIX + scope)
        continue
      failed[scope] = error
      continue
    changed = True
    if commands:
      await synced.put(SYNCED_PREFIX + scope, _Synced(hash=digest))
    else:
      await synced.delete(SYNCED_PREFIX + scope)
    logger.info("Synced %d commands for %s", len(commands), scope)
  for key, declared in view.items():
    if not any(scope in failed for scope in scopes_of.get(key, [])):
      await declarations.mark_applied(key, declared.hash)
  if failed:
    raise SyncFailed(failed)
  return changed


async def _overwrite(
  http: Any, application_id: str, scope: str, commands: list[JsonValue]
) -> None:
  if scope == "global":
    await http.call(
      "bulk_set_application_commands",
      path={"application_id": application_id},
      body=commands,
    )
  else:
    await http.call(
      "bulk_set_guild_application_commands",
      path={"application_id": application_id, "guild_id": scope},
      body=commands,
    )


async def _drifted(
  http: Any, application_id: str, scope: str, commands: list[JsonValue]
) -> bool:
  """Whether Discord has different commands (by type and name) than we want."""
  if scope == "global":
    live = await http.call(
      "list_application_commands", path={"application_id": application_id}
    )
  else:
    live = await http.call(
      "list_guild_application_commands",
      path={"application_id": application_id, "guild_id": scope},
    )

  def identities(items: Any) -> list[tuple[int, str]]:
    return sorted(
      (item.get("type", 1), item["name"])
      for item in items
      if item.get("type", 1) != ENTRY_POINT
    )

  return identities(live) != identities(commands)


def _unreachable(error: Exception) -> bool:
  """Discord refused the scope itself: the bot is not in that guild."""
  from micro.discord import DiscordAPIError

  return isinstance(error, DiscordAPIError) and error.status in (403, 404)
