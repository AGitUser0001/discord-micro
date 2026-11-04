"""Command sync: registers converged command definitions with Discord."""

import asyncio
import hashlib
import json
import logging
from typing import Any, cast

from pydantic import BaseModel, ConfigDict, JsonValue

from micro import subjects
from micro.coordination import Declarations
from micro.runtime import Component

logger = logging.getLogger("micro")

SYNC_LOCK = "commands.sync"
SYNCED_PREFIX = "synced.commands."


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
  changes, under a cluster lock, so running several replicas is safe.
  """

  kind = "command-sync"

  def __init__(self, name: str = "command-sync") -> None:
    super().__init__(name)
    self._changed = asyncio.Event()
    self.synced = asyncio.Event()
    """Set after each successful pass."""
    self._application_id: str | None = None

  async def on_start(self) -> None:
    self._unwatch = self.runtime.directory.on_change(self._changed.set)
    self._changed.set()
    self.spawn(self._loop(), name="sync")

  async def on_close(self) -> None:
    self._unwatch()

  async def _loop(self) -> None:
    delay = 0.5
    while self.active:
      await self._changed.wait()
      self._changed.clear()
      try:
        await self.sync()
        delay = 0.5
      except asyncio.CancelledError:
        raise
      except Exception as exc:
        logger.info("Command sync will retry: %s", exc)
        await asyncio.sleep(delay)
        delay = min(delay * 2, 30.0)
        self._changed.set()

  async def sync(self) -> bool:
    """One pass; returns True if Discord's commands changed."""
    from micro.discord import DiscordHTTPClient

    http = DiscordHTTPClient(self.runtime)
    if self._application_id is None:
      self._application_id = str((await http.call("get_my_application"))["id"])
    locks = await self.runtime.locks()
    async with locks.hold(SYNC_LOCK, ttl=30):
      changed = await sync_commands(self.runtime, http, self._application_id)
    self.synced.set()
    return changed


async def sync_commands(runtime: Any, http: Any, application_id: str) -> bool:
  """Bulk-overwrite every scope whose converged commands changed (hold SYNC_LOCK)."""
  declarations = Declarations(runtime, "commands")
  view = await declarations.view()
  scopes: dict[str, dict[str, JsonValue]] = {}
  for key, declared in view.items():
    definition = dict(cast(dict[str, Any], declared.document))
    guilds = definition.pop("guild_ids", None) or []
    for scope in [str(guild) for guild in guilds] if guilds else ["global"]:
      scopes.setdefault(scope, {})[key] = definition
  synced = await runtime.table(subjects.STATE_BUCKET, _Synced)
  previous = {
    key.removeprefix(SYNCED_PREFIX): entry.value.hash
    for key, entry in (await synced.items(SYNCED_PREFIX + ">")).items()
  }
  changed = False
  for scope in sorted(set(scopes) | set(previous)):
    commands: list[JsonValue] = [
      scopes.get(scope, {})[key] for key in sorted(scopes.get(scope, {}))
    ]
    digest = hashlib.sha256(
      json.dumps(commands, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    if previous.get(scope) == digest:
      continue
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
    changed = True
    if commands:
      await synced.put(SYNCED_PREFIX + scope, _Synced(hash=digest))
    else:
      await synced.delete(SYNCED_PREFIX + scope)
    logger.info("Synced %d commands for %s", len(commands), scope)
  for key, declared in view.items():
    await declarations.mark_applied(key, declared.hash)
  return changed
