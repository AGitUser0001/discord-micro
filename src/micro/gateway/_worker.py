import asyncio
import json
import logging
import math
import os
from collections.abc import Callable, Mapping
from contextlib import suppress
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from nats.aio.msg import Msg
from nats.aio.subscription import Subscription
from pydantic import BaseModel, ValidationError

from micro import subjects
from micro.config import Applied, Config
from micro.coordination import Locks, Table, Versioned
from micro.runtime import Component, Presence

from ._connection import HikariShard, ShardHost, ShardSession
from ._control import (
  GatewayGeneration,
  GuildMembersRequest,
  PresenceUpdate,
  ShardLease,
  VoiceStateUpdate,
)
from ._events import (
  CONNECTION_HEADER,
  GENERATION_HEADER,
  SHARD_HEADER,
  ConnectionEvent,
  ConnectionEventKind,
)
from ._settings import SETTINGS_NAME, GatewaySettings

if TYPE_CHECKING:
  import hikari

logger = logging.getLogger("micro")

WORKER_KIND = "gateway"
DESIRED_KEY = "generation.desired"
ACTIVE_KEY = "generation.active"
PRESENCE_KEY = "presence"

type SessionFactory = Callable[[ShardHost, int, int, int], ShardSession]


@dataclass(eq=False)
class _Held:
  """A shard session this worker runs."""

  session: ShardSession
  key: str
  revision: int | None
  """Lease revision when this worker owns the shard; None while on standby."""
  ready: bool = False
  releasing: bool = False
  starter: asyncio.Task[None] | None = None
  controls: list[Subscription] = field(default_factory=list)
  publishing: bool = False

  @property
  def owned(self) -> bool:
    return self.revision is not None


def lease_key(generation: int, shard_id: int) -> str:
  """The table key of a shard's lease."""
  return f"{generation}.{shard_id}"


def _plain(value: object) -> object:
  """Hikari hands over each payload as a read-only mapping, which json refuses."""
  if isinstance(value, Mapping):
    return dict(value)
  raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def guild_of(name: str, payload: Mapping[str, Any]) -> str | None:
  """The guild id a dispatch belongs to (for its subject), or None."""
  guild = payload.get("guild_id")
  if (
    guild is None
    and name.startswith("GUILD_")
    and name
    in {
      "GUILD_CREATE",
      "GUILD_UPDATE",
      "GUILD_DELETE",
    }
  ):
    guild = payload.get("id")
  return guild if isinstance(guild, str) and guild.isdecimal() else None


def format_intents(value: int) -> str:
  """Intent names for a number (`guilds,guild_members`), or `none`."""
  import hikari

  names = [
    flag.name.lower()
    for flag in hikari.Intents
    if flag.name and flag.value and flag.value & (flag.value - 1) == 0 and value & flag
  ]
  return ",".join(names) or "none"


def parse_intents(text: str) -> hikari.Intents:
  """Intents from names or numbers: `unprivileged,message_content` or `33280`.

  `unprivileged`, `privileged` and `all` stand for hikari's groups; anything
  else is an intent name such as `message_content` or `guild_members`.
  """
  import difflib

  import hikari

  groups = {
    "UNPRIVILEGED": hikari.Intents.ALL_UNPRIVILEGED,
    "PRIVILEGED": hikari.Intents.ALL_PRIVILEGED,
  }
  result = hikari.Intents.NONE
  for part in text.replace("|", ",").split(","):
    item = part.strip()
    if not item:
      continue
    if item.isdecimal():
      result |= hikari.Intents(int(item))
      continue
    name = item.upper().replace(" ", "_").replace("-", "_")
    found = groups.get(name) or hikari.Intents.__members__.get(name)
    if found is None:
      close = difflib.get_close_matches(
        name, [*groups, *hikari.Intents.__members__], n=1
      )
      hint = f" Did you mean {close[0].lower()}?" if close else ""
      raise ValueError(f"Unknown intent {item!r}.{hint}")
    result |= found
  return result


class GatewayWorker(Component):
  """A self-balancing Discord Gateway worker.

  Workers share shards through TTL leases: each claims its fair share, takes over
  expired or released shards, and hands shards over without a gap (the new
  owner connects on standby and takes the lease once READY). Only the owner of
  a shard in the active generation publishes dispatches. Changing the shard
  count or rolling every connection is a new generation, written with
  `GatewayControl`; workers start it beside the old one and flip publishing once
  every new shard is READY.
  """

  kind = WORKER_KIND

  def __init__(
    self,
    token: str | None = None,
    *,
    shard_count: int = 1,
    max_concurrency: int = 1,
    lease_ttl: float = 10.0,
    name: str = "gateway",
    api_url: str | None = None,
    session_factory: SessionFactory = HikariShard,
    networked: bool = False,
  ) -> None:

    token = token if token is not None else os.environ.get("DISCORD_TOKEN")
    if not token:
      raise ValueError("A Discord token is required (argument or DISCORD_TOKEN).")
    if not 1 <= shard_count <= 4096:
      raise ValueError("shard_count must be between 1 and 4096.")
    if max_concurrency < 1:
      raise ValueError("max_concurrency must be positive.")
    if lease_ttl < 3:
      raise ValueError("lease_ttl must be at least 3 seconds.")
    super().__init__(name)
    self.token = token
    self.api_url = api_url or os.environ.get("DISCORD_API_URL")
    self.initial_shard_count = shard_count
    self.max_concurrency = max_concurrency
    self.lease_ttl = lease_ttl
    self.networked = networked
    self.settings: Config[GatewaySettings] | None = None
    """The shared settings (set when `networked`, once started)."""
    self._bootstrap = GatewaySettings(
      max_concurrency=max_concurrency, lease_ttl=lease_ttl
    )
    self._generation_intents: dict[int, int | None] = {}
    self._factory = session_factory
    self.address = subjects.token(os.urandom(8).hex())
    self._held: dict[str, _Held] = {}
    self._wake = asyncio.Event()
    self._lock = asyncio.Lock()
    self._presence: Presence | None = None
    self._desired: GatewayGeneration | None = None
    self._active: GatewayGeneration | None = None
    self._status: PresenceUpdate | None = None
    self._leases: dict[str, Versioned[ShardLease]] = {}
    self._released = asyncio.Event()

  # Introspection ---------------------------------------------------------------

  def intents_for(self, generation: int) -> hikari.Intents:
    """The intents a generation connects with: the one it records, else Discord's
    unprivileged set. Intents are changed only by `GatewayControl.set_intents`."""
    import hikari

    chosen = self._generation_intents.get(generation)
    return hikari.Intents.ALL_UNPRIVILEGED if chosen is None else hikari.Intents(chosen)

  @property
  def owned_shards(self) -> dict[int, tuple[int, ...]]:
    """Shards this worker owns, per generation."""
    owned: dict[int, list[int]] = {}
    for held in self._held.values():
      if held.owned:
        owned.setdefault(held.session.generation, []).append(held.session.shard_id)
    return {gen: tuple(sorted(shards)) for gen, shards in owned.items()}

  @property
  def publishing_shards(self) -> tuple[int, ...]:
    """Shards this worker currently publishes dispatches for."""
    return tuple(
      sorted(h.session.shard_id for h in self._held.values() if h.publishing)
    )

  @property
  def ready(self) -> bool:
    """Whether every shard this worker owns is READY."""
    return self.accepting and all(h.ready for h in self._held.values() if h.owned)

  # Lifecycle -------------------------------------------------------------------

  async def on_start(self) -> None:
    """Join the deployment, watch generations and presence, and start claiming shards."""
    runtime = self.runtime
    if self.networked:
      self.settings = Config(
        runtime, SETTINGS_NAME, GatewaySettings, bootstrap=self._bootstrap
      )
      self.settings.on_change(self._settings_applied)
      await self.settings.start()
      self._use_settings(self.settings.value)
    self._generations = await runtime.table(subjects.GATEWAY_BUCKET, GatewayGeneration)
    self._statuses = await runtime.table(subjects.GATEWAY_BUCKET, PresenceUpdate)
    self._shards: Table[ShardLease] = await runtime.table(
      subjects.SHARDS_BUCKET, ShardLease, ttl_markers=True
    )
    self._locks: Locks = await runtime.locks()
    initial = GatewayGeneration(id=1, shard_count=self.initial_shard_count)
    await self._generations.create(DESIRED_KEY, initial)
    await self._generations.create(ACTIVE_KEY, initial)
    self._presence = await runtime.register(
      self, id=self.address, metadata={"max_concurrency": self.max_concurrency}
    )
    self._unwatch = runtime.directory.on_change(
      self._wake.set, watching=lambda: self._peers()
    )
    self.spawn(self._watch_generations(), name="watch.generations")
    self.spawn(self._watch_leases(), name="watch.leases")
    self.spawn(self._control_loop(), name="control")

  async def on_drain(self) -> None:
    # Leave presence so peers recount their fair share, then hand every shard over.
    """Leave presence and hand every shard over without a gap."""
    if self._presence is not None:
      await self.runtime.unregister(self._presence)
      self._presence = None
    self._wake.set()
    while any(h.owned for h in self._held.values()) and self._peers():
      self._released.clear()
      self._wake.set()
      await self._released.wait()

  async def on_close(self) -> None:
    """Disconnect every shard and release its lease."""
    self._unwatch()
    if self.settings is not None:
      await self.settings.close()
    if self._presence is not None:
      await self.runtime.unregister(self._presence)
      self._presence = None
    for held in tuple(self._held.values()):
      await self._stop(held, delete_lease=True)

  # Networked settings ----------------------------------------------------------

  def _use_settings(self, settings: GatewaySettings) -> None:
    """Take the shared settings."""
    self.max_concurrency = settings.max_concurrency
    self.lease_ttl = settings.lease_ttl

  async def _settings_applied(self, applied: Applied[GatewaySettings]) -> None:
    self._use_settings(applied.new)
    if applied.new.max_concurrency != applied.old.max_concurrency and self._presence:
      await self._presence.update({"max_concurrency": self.max_concurrency})
    self._wake.set()

  # Watches ---------------------------------------------------------------------

  async def _watch_generations(self) -> None:
    async for change in self._generations.watch("generation.*"):
      if change is not None and change.value is not None:
        self._generation_intents[change.value.id] = change.value.intents
        if change.key == DESIRED_KEY:
          self._desired = change.value
        elif change.key == ACTIVE_KEY:
          self._active = change.value
      self._wake.set()

  async def _watch_leases(self) -> None:
    async for change in self._shards.watch():
      if change is None:
        self._wake.set()
        continue
      known = self._leases.get(change.key)
      if change.value is None:
        self._leases.pop(change.key, None)
        self._wake.set()
        continue
      self._leases[change.key] = Versioned(change.value, change.revision)
      # A renewal rewrites the same lease, ours or a peer's; waking for it would make
      # every renewal trigger the next one. Wake only when ownership or state changed.
      if known is None or known.value != change.value:
        self._wake.set()
    # Unreachable unless the watch ends.

  async def _watch_status(self) -> None:
    async for change in self._statuses.watch(PRESENCE_KEY):
      if change is not None and change.value is not None:
        self._status = change.value
        for held in tuple(self._held.values()):
          if held.ready:
            await self._apply_status(held)

  # Control loop ----------------------------------------------------------------

  async def _control_loop(self) -> None:
    self.spawn(self._watch_status(), name="watch.status")
    while True:
      with suppress(TimeoutError):
        await asyncio.wait_for(self._wake.wait(), self.lease_ttl / 3)
      self._wake.clear()
      try:
        async with self._lock:
          await self._reconcile()
      except asyncio.CancelledError:
        raise
      except Exception:
        logger.exception("Gateway reconciliation failed")
      self._released.set()

  def _peers(self) -> list[str]:
    return sorted(
      entry.id
      for entry in self.runtime.directory.entries(WORKER_KIND)
      if entry.id != self.address
    )

  def _workers(self) -> list[str]:
    workers = self._peers()
    if self.accepting:
      workers.append(self.address)
    return sorted(workers)

  async def _reconcile(self) -> None:
    desired, active = self._desired, self._active
    if desired is None or active is None:
      return
    generations = {desired.id: desired, active.id: active}

    # Sessions of retired generations close.
    for held in tuple(self._held.values()):
      if held.session.generation not in generations:
        await self._stop(held, delete_lease=True)

    await self._renew()

    workers = self._workers()
    for generation in generations.values():
      if self.accepting and workers:
        await self._balance(generation, workers)
    await self._take_over()

    if desired.id != active.id and self._generation_ready(desired):
      flipped = await self._flip(desired)
      if flipped:
        active = desired
        self._active = desired

    for held in tuple(self._held.values()):
      await self._set_publishing(
        held, held.owned and held.session.generation == active.id
      )

  async def _renew(self) -> None:
    for held in tuple(self._held.values()):
      if not held.owned:
        continue
      current = self._leases.get(held.key)
      if current is not None and current.value.owner != self.address:
        logger.info("Lease %s was taken over", held.key)
        await self._stop(held, delete_lease=False)
        continue
      releasing = held.releasing or not self.accepting
      lease = ShardLease(
        owner=self.address,
        ready=held.ready,
        releasing=releasing,
        connection_id=held.session.connection_id,
      )
      assert held.revision is not None
      revision = await self._shards.update(
        held.key, lease, revision=held.revision, ttl=self.lease_ttl
      )
      if revision is None:
        logger.info("Lease %s was taken over", held.key)
        await self._stop(held, delete_lease=False)
        continue
      held.revision = revision
      held.releasing = releasing
      self._leases[held.key] = Versioned(lease, revision)

  async def _balance(self, generation: GatewayGeneration, workers: list[str]) -> None:
    count = generation.shard_count
    share = math.ceil(count / len(workers))
    floor = count // len(workers)
    mine = [
      held for held in self._held.values() if held.session.generation == generation.id
    ]
    owners: dict[str, int] = {}
    for shard_id in range(count):
      lease = self._leases.get(lease_key(generation.id, shard_id))
      if lease is not None:
        owners[lease.value.owner] = owners.get(lease.value.owner, 0) + 1

    # Claim free shards, then shards others are releasing, up to the fair share.
    candidates: list[tuple[int, Versioned[ShardLease] | None]] = []
    for shard_id in range(count):
      key = lease_key(generation.id, shard_id)
      if key in self._held:
        continue
      lease = self._leases.get(key)
      if lease is None:
        candidates.insert(0, (shard_id, None))
      elif lease.value.releasing and lease.value.owner != self.address:
        candidates.append((shard_id, lease))
    for shard_id, lease in candidates:
      if len(mine) >= share:
        break
      key = lease_key(generation.id, shard_id)
      if lease is None:
        claim = ShardLease(owner=self.address)
        revision = await self._shards.create(key, claim, ttl=self.lease_ttl)
        if revision is None:
          continue
        self._leases[key] = Versioned(claim, revision)
        held = self._open(generation, shard_id, revision)
      else:
        held = self._open(generation, shard_id, None)
      mine.append(held)

    # Over share while a peer is under: release one shard at a time.
    owned = [held for held in mine if held.owned]
    over_share = len(owned) > share or (
      len(owned) > floor and any(owners.get(w, 0) < floor for w in workers)
    )
    if over_share and not any(held.releasing for held in owned):
      victim = max(owned, key=lambda held: held.session.shard_id)
      victim.releasing = True
      self._wake.set()

  async def _take_over(self) -> None:
    """Standby sessions take the lease once READY (gap-free handoff)."""
    for held in tuple(self._held.values()):
      if held.owned:
        continue
      lease = self._leases.get(held.key)
      if lease is not None and not lease.value.releasing:
        await self._stop(held, delete_lease=False)
        continue
      if not held.ready:
        continue
      claim = ShardLease(
        owner=self.address, ready=True, connection_id=held.session.connection_id
      )
      # Publish before claiming: an overlap duplicates events, a gap would lose them.
      active = self._active
      overlap = active is not None and held.session.generation == active.id
      if overlap:
        await self._set_publishing(held, True)
      if lease is None:
        revision = await self._shards.create(held.key, claim, ttl=self.lease_ttl)
      else:
        revision = await self._shards.update(
          held.key, claim, revision=lease.revision, ttl=self.lease_ttl
        )
      if revision is None:
        if overlap:
          await self._set_publishing(held, False)
        continue
      held.revision = revision
      self._leases[held.key] = Versioned(claim, revision)

  def _generation_ready(self, generation: GatewayGeneration) -> bool:
    for shard_id in range(generation.shard_count):
      lease = self._leases.get(lease_key(generation.id, shard_id))
      if lease is None or not lease.value.ready:
        return False
    return True

  async def _flip(self, desired: GatewayGeneration) -> bool:
    current = await self._generations.get(ACTIVE_KEY)
    if current is None or current.value.id == desired.id:
      return current is not None
    if current.value.id > desired.id:
      return False
    revision = await self._generations.update(
      ACTIVE_KEY, desired, revision=current.revision
    )
    if revision is not None:
      logger.info("Gateway generation %d is now publishing", desired.id)
    return revision is not None

  # Sessions --------------------------------------------------------------------

  def _open(
    self, generation: GatewayGeneration, shard_id: int, revision: int | None
  ) -> _Held:
    self._generation_intents[generation.id] = generation.intents
    session = self._factory(self, generation.id, shard_id, generation.shard_count)
    held = _Held(session, lease_key(generation.id, shard_id), revision)
    self._held[held.key] = held
    held.starter = self.spawn(self._start(held), name=f"shard.{held.key}")
    return held

  async def _start(self, held: _Held) -> None:
    bucket = held.session.shard_id % self.max_concurrency
    await self._locks.gate(f"identify.{bucket}", ttl=5.0)
    if self._held.get(held.key) is not held:
      return
    await held.session.start()

  async def _stop(self, held: _Held, *, delete_lease: bool) -> None:
    if self._held.get(held.key) is held:
      del self._held[held.key]
    await self._set_publishing(held, False)
    if held.starter is not None and not held.starter.done():
      held.starter.cancel()
      with suppress(asyncio.CancelledError, Exception):
        await held.starter
    try:
      await held.session.close()
    except Exception:
      logger.exception("Closing shard %s failed", held.key)
    if delete_lease and held.revision is not None:
      with suppress(Exception):
        await self._shards.delete(held.key, revision=held.revision)
        self._leases.pop(held.key, None)

  async def _set_publishing(self, held: _Held, publishing: bool) -> None:
    if held.publishing == publishing:
      return
    held.publishing = publishing
    shard_id = held.session.shard_id
    if publishing:
      nats = self.runtime.nats
      held.controls = [
        await nats.subscribe(
          subjects.gateway_control(shard_id, "members"),
          queue="micro.gateway",
          cb=self._control(
            held, GuildMembersRequest, lambda s, c: s.request_guild_members(c)
          ),
        ),
        await nats.subscribe(
          subjects.gateway_control(shard_id, "voice"),
          queue="micro.gateway",
          cb=self._control(
            held, VoiceStateUpdate, lambda s, c: s.update_voice_state(c)
          ),
        ),
      ]
    else:
      controls, held.controls = held.controls, []
      for subscription in controls:
        with suppress(Exception):
          await subscription.unsubscribe()

  def _control[ModelT: BaseModel](
    self,
    held: _Held,
    model: type[ModelT],
    action: Callable[[ShardSession, ModelT], Any],
  ) -> Callable[[Msg], Any]:
    async def callback(message: Msg) -> None:
      try:
        command = model.model_validate_json(message.data)
        await action(held.session, command)
        body, status = b"{}", "ok"
      except ValidationError as exc:
        body = json.dumps({"code": "invalid_input", "message": str(exc)}).encode()
        status = "error"
      except Exception as exc:
        body = json.dumps({"code": "handler_failed", "message": str(exc)}).encode()
        status = "error"
      if message.reply:
        await self.runtime.nats.publish(
          message.reply, body, headers={"Micro-Status": status}
        )

    return callback

  async def _apply_status(self, held: _Held) -> None:
    if self._status is None:
      return
    try:
      await held.session.update_presence(self._status)
    except Exception:
      logger.warning("Could not apply presence to %s", held.key, exc_info=True)

  # ShardHost -------------------------------------------------------------------

  async def on_dispatch(
    self, session: ShardSession, name: str, payload: Mapping[str, Any]
  ) -> None:
    """Publish one Gateway dispatch (to the dispatch subject if this connection owns the shard, else standby)."""
    held = self._held.get(lease_key(session.generation, session.shard_id))
    publishing = held is not None and held.session is session and held.publishing
    guild = guild_of(name, payload)
    subject = (
      subjects.dispatch(name, guild) if publishing else subjects.standby(name, guild)
    )
    headers = {
      SHARD_HEADER: str(session.shard_id),
      GENERATION_HEADER: str(session.generation),
    }
    if session.connection_id is not None:
      headers[CONNECTION_HEADER] = session.connection_id
    body = json.dumps(payload, separators=(",", ":"), default=_plain).encode()
    await self.runtime.jetstream.publish(
      subject, body, stream=subjects.EVENTS_STREAM, headers=headers
    )

  async def on_connection(
    self, session: ShardSession, kind: ConnectionEventKind
  ) -> None:
    """Publish a connection lifecycle event and re-apply the bot's presence when it is ready."""
    held = self._held.get(lease_key(session.generation, session.shard_id))
    if held is not None and held.session is session:
      if kind in (ConnectionEventKind.READY, ConnectionEventKind.RESUMED):
        held.ready = True
        await self._apply_status(held)
      elif kind in (
        ConnectionEventKind.DISCONNECTED,
        ConnectionEventKind.INVALIDATED,
        ConnectionEventKind.CLOSED,
      ):
        held.ready = False
      self._wake.set()
    event = ConnectionEvent(
      kind=kind,
      shard_id=session.shard_id,
      generation=session.generation,
      connection_id=session.connection_id,
      worker=self.address,
    )
    await self.runtime.jetstream.publish(
      subjects.connection(session.shard_id),
      event.model_dump_json().encode(),
      stream=subjects.EVENTS_STREAM,
    )
