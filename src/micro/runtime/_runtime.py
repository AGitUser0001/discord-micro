import asyncio
import os
import signal
import socket
from collections.abc import Callable, Sequence
from contextlib import suppress
from dataclasses import dataclass
from types import TracebackType
from typing import TYPE_CHECKING, Any, Self
from uuid import uuid4

import nats
from nats.aio.client import Client as NATS
from nats.aio.msg import Msg
from nats.js.api import RetentionPolicy, StorageType, StreamConfig
from nats.js.client import JetStreamContext
from nats.js.errors import BadRequestError
from nats.js.object_store import ObjectStore
from pydantic import BaseModel, JsonValue

from micro import log, subjects
from micro.coordination import LockHolder, Locks, Table

if TYPE_CHECKING:
  from micro.config import Config

from ._component import Component, ComponentState
from ._presence import Directory, Presence, Registration, registration_id

DEFAULT_NATS_URL = "nats://127.0.0.1:4222"
RUNTIME_KIND = "runtime"
PAYLOAD_HEADER = "Micro-Payload"
"""Names the object holding a request or reply body too large for one message."""
PAYLOAD_TTL = 3600.0
"""Seconds an unread large payload is kept (readers delete them immediately)."""
_HEADROOM = 64 * 1024


@dataclass(frozen=True, slots=True)
class Reply:
  """A NATS reply: its body bytes and headers."""

  data: bytes
  headers: dict[str, str]


def default_servers() -> tuple[str, ...]:
  """The NATS servers from `MICRO_NATS_URL` (comma separated), else the local default."""
  value = os.environ.get("MICRO_NATS_URL", DEFAULT_NATS_URL)
  return tuple(server.strip() for server in value.split(",") if server.strip())


class Runtime:
  """One process's connection to a Micro deployment.

  A runtime owns a single NATS connection, its JetStream context, and the shared
  tables, and hosts any number of components. The same components run in one
  runtime or spread across many processes; only configuration changes.
  """

  def __init__(
    self,
    servers: str | Sequence[str] | None = None,
    *,
    name: str = "micro",
    replicas: int = 1,
    presence_ttl: float = 10.0,
    storage: StorageType = StorageType.FILE,
    **connect_options: Any,
  ) -> None:
    if isinstance(servers, str):
      servers = (servers,)
    self.servers = tuple(servers) if servers is not None else default_servers()
    if not self.servers:
      raise ValueError("A runtime needs at least one NATS server.")
    if replicas < 1:
      raise ValueError("replicas must be at least 1.")
    if presence_ttl < 3:
      raise ValueError("presence_ttl must be at least 3 seconds.")
    self.name = name
    self.instance = uuid4().hex
    self.replicas = replicas
    self.presence_ttl = presence_ttl
    self.storage = storage
    self._connect_options = connect_options
    self._nats: NATS | None = None
    self._jetstream: JetStreamContext | None = None
    self._tables: dict[str, Table[Any]] = {}
    self._directory: Directory | None = None
    self._components: list[Component] = []
    self._presences: dict[int, Presence] = {}
    self._started = False
    self._payloads: ObjectStore | None = None
    self._configs: list[Config[Any]] = []

  @property
  def nats(self) -> NATS:
    """The underlying NATS client (raises before the runtime starts)."""
    if self._nats is None:
      raise RuntimeError("Runtime has not started.")
    return self._nats

  @property
  def jetstream(self) -> JetStreamContext:
    """The JetStream context (raises before the runtime starts)."""
    if self._jetstream is None:
      raise RuntimeError("Runtime has not started.")
    return self._jetstream

  @property
  def directory(self) -> Directory:
    """The live presence directory (raises before the runtime starts)."""
    if self._directory is None:
      raise RuntimeError("Runtime has not started.")
    return self._directory

  @property
  def components(self) -> tuple[Component, ...]:
    """The components this runtime hosts, in start order."""
    return tuple(self._components)

  @property
  def ready(self) -> bool:
    """Whether the runtime is connected and every hosted component is ready."""
    return (
      self._started
      and self._nats is not None
      and self._nats.is_connected
      and all(component.ready for component in self._components)
    )

  async def start(self) -> None:
    """Connect to NATS and open the shared tables and presence directory."""
    if self._started:
      return
    if any(server.startswith(("ws://", "wss://")) for server in self.servers):
      from micro._slim import restore_websocket_transport

      restore_websocket_transport()
    self._nats = await nats.connect(
      list(self.servers), name=self.name, **self._connect_options
    )
    self._jetstream = self._nats.jetstream()
    await self.ensure_stream(
      subjects.EVENTS_STREAM,
      subjects.EVENT_STREAM_SUBJECTS,
      retention=RetentionPolicy.INTEREST,
      retire=subjects.RETIRED_EVENT_STREAM_SUBJECTS,
    )
    presence = await self.table(
      subjects.PRESENCE_BUCKET, Registration, ttl_markers=True
    )
    self._directory = Directory(presence)
    await self._directory.start()
    self._started = True

  async def add(self, *components: Component) -> None:
    """Start components in this runtime (starting the runtime if needed)."""
    await self.start()
    for component in components:
      await component.start(self)
      self._components.append(component)

  async def drain(self) -> None:
    """Drain components in reverse start order; each finishes in-flight work."""
    for component in reversed(self._components):
      try:
        await component.drain()
      except Exception:
        log.exception("Draining %s failed", component.name)

  async def close(self) -> None:
    """Close hosted components and disconnect."""
    for component in reversed(self._components):
      try:
        await component.close()
      except Exception:
        log.exception("Closing %s failed", component.name)
    self._components.clear()
    for config in reversed(self._configs):
      await config.close()
    self._configs.clear()
    for presence in tuple(self._presences.values()):
      await presence.stop()
    self._presences.clear()
    if self._directory is not None:
      await self._directory.close()
      self._directory = None
    if self._nats is not None and not self._nats.is_closed:
      with suppress(Exception):
        await self._nats.drain()
    self._nats = None
    self._jetstream = None
    self._tables.clear()
    self._started = False

  async def __aenter__(self) -> Self:
    await self.start()
    return self

  async def __aexit__(
    self,
    exc_type: type[BaseException] | None,
    exc: BaseException | None,
    traceback: TracebackType | None,
  ) -> None:
    await self.drain()
    await self.close()

  async def serve(self, *components: Component) -> None:
    """Host components until SIGINT/SIGTERM, then drain and close.

    A second signal skips the remaining drain.
    """
    loop = asyncio.get_running_loop()
    stop = asyncio.Event()
    signals = (signal.SIGINT, signal.SIGTERM)
    for sig in signals:
      with suppress(NotImplementedError, RuntimeError):
        loop.add_signal_handler(sig, stop.set)
    try:
      await self.add(*components)
      await self.register(
        kind=RUNTIME_KIND,
        name=self.name,
        id=self.instance,
        metadata={
          "pid": os.getpid(),
          "host": socket.gethostname(),
          "components": [component.name for component in self._components],
        },
      )
      log.info(
        "Micro runtime %s hosting %s",
        self.instance,
        ", ".join(component.name for component in self._components),
      )
      await stop.wait()
      stop.clear()
      draining = asyncio.create_task(self.drain())
      interrupted = asyncio.create_task(stop.wait())
      await asyncio.wait((draining, interrupted), return_when=asyncio.FIRST_COMPLETED)
      for task in (draining, interrupted):
        task.cancel()
      await asyncio.gather(draining, interrupted, return_exceptions=True)
    finally:
      for sig in signals:
        with suppress(NotImplementedError, RuntimeError):
          loop.remove_signal_handler(sig)
      await self.close()

  # Request/reply with bodies of any size --------------------------------------------

  async def request(
    self,
    subject: str,
    body: bytes,
    *,
    headers: dict[str, str] | None = None,
    timeout: float,
  ) -> Reply:
    """A NATS request whose body and reply may exceed the server's message limit."""
    data, sent = await self._encode(body, headers)
    reply = await self.nats.request(subject, data, timeout=timeout, headers=sent)
    return Reply(await self.payload(reply), dict(reply.headers or {}))

  async def respond(
    self, message: Msg, body: bytes, *, headers: dict[str, str] | None = None
  ) -> None:
    """Reply to a request (any size); does nothing for messages without a reply."""
    if message.reply:
      data, sent = await self._encode(body, headers)
      await self.nats.publish(message.reply, data, headers=sent)

  async def payload(self, message: Msg) -> bytes:
    """A received body, fetching (and deleting) it if it travelled as an object."""
    name = (message.headers or {}).get(PAYLOAD_HEADER)
    if not name:
      return message.data
    store = await self._payload_store()
    result = await store.get(name)
    with suppress(Exception):
      await store.delete(name)
    return result.data or b""

  async def _encode(
    self, body: bytes, headers: dict[str, str] | None
  ) -> tuple[bytes, dict[str, str] | None]:
    if len(body) <= self.nats.max_payload - _HEADROOM:
      return body, headers
    name = uuid4().hex
    await (await self._payload_store()).put(name, body)
    return b"", {**(headers or {}), PAYLOAD_HEADER: name}

  async def _payload_store(self) -> ObjectStore:
    if self._payloads is None:
      try:
        self._payloads = await self.jetstream.create_object_store(
          subjects.PAYLOADS_BUCKET,
          ttl=PAYLOAD_TTL,
          storage=self.storage,
          replicas=self.replicas,
        )
      except BadRequestError:
        self._payloads = await self.jetstream.object_store(subjects.PAYLOADS_BUCKET)
    return self._payloads

  async def ensure_stream(
    self,
    name: str,
    stream_subjects: Sequence[str],
    *,
    retention: RetentionPolicy,
    retire: Sequence[str] = (),
    allow_msg_ttl: bool = False,
    allow_msg_schedules: bool = False,
    max_msgs_per_subject: int | None = None,
    duplicate_window: float | None = None,
  ) -> None:
    """Create a stream, or bring an existing one up to date without losing data.

    Missing subjects are added and `retire`d subjects removed, so a rolling
    upgrade of Micro can move subjects between streams.
    """
    config = StreamConfig(
      name=name,
      subjects=list(stream_subjects),
      retention=retention,
      storage=self.storage,
      num_replicas=self.replicas,
      allow_msg_ttl=allow_msg_ttl or None,
      allow_msg_schedules=allow_msg_schedules or None,
      max_msgs_per_subject=max_msgs_per_subject or -1,
      duplicate_window=duplicate_window or 0,
    )
    try:
      await self.jetstream.add_stream(config)
      return
    except BadRequestError:
      pass
    info = await self.jetstream.stream_info(name)
    existing = set(info.config.subjects or ())
    wanted = (existing | set(stream_subjects)) - set(retire)
    changed = wanted != existing
    if allow_msg_ttl and not info.config.allow_msg_ttl:
      info.config.allow_msg_ttl = True
      changed = True
    if allow_msg_schedules and not info.config.allow_msg_schedules:
      info.config.allow_msg_schedules = True
      changed = True
    if changed:
      info.config.subjects = sorted(wanted)
      await self.jetstream.update_stream(info.config)

  async def table[T](
    self,
    bucket: str,
    value_type: type[T] | Any,
    *,
    ttl_markers: bool = False,
  ) -> Table[T]:
    """Open (creating if needed) a typed table.

    `ttl_markers` makes per-key TTL expiry visible to watchers.
    """
    if bucket in self._tables:
      return Table(self._tables[bucket]._store, value_type)  # pyright: ignore[reportPrivateUsage]
    try:
      store = await self.jetstream.create_key_value(
        bucket=bucket,
        storage=self.storage,
        replicas=self.replicas,
        limit_marker_ttl=1.0 if ttl_markers else None,
      )
    except BadRequestError:
      # The bucket already exists with other settings (for example replicas).
      store = await self.jetstream.key_value(bucket)
    table = Table[T](store, value_type)
    self._tables[bucket] = table
    return table

  async def config[M: BaseModel](
    self,
    name: str,
    model: type[M],
    *,
    bootstrap: M | Callable[[], M] | None = None,
    seed: bool = True,
  ) -> Config[M]:
    """Open and start a shared, typed configuration document (see `micro.config`).

    Asking again for the same name and model returns the one already open. It is closed with the runtime. `bootstrap` is this process's own settings: what
    `value` returns before the first load and the document written if none exists.
    """
    from micro.config import Config

    for existing in self._configs:
      if existing.name == name and existing.model is model:
        return existing
    config = Config(self, name, model, bootstrap=bootstrap, seed=seed)
    await config.start()
    self._configs.append(config)
    return config

  async def locks(self) -> Locks:
    """The cluster-wide `Locks` for this deployment."""
    return Locks(
      await self.table(subjects.LOCKS_BUCKET, LockHolder, ttl_markers=True),
      self.instance,
    )

  async def register(
    self,
    component: Component | None = None,
    *,
    kind: str | None = None,
    name: str | None = None,
    metadata: dict[str, JsonValue] | None = None,
    id: str | None = None,
  ) -> Presence:
    """Advertise a component (or any `kind`/`name`) in the presence table."""
    kind = kind or (component.kind if component is not None else None)
    name = name or (component.name if component is not None else None)
    if kind is None or name is None:
      raise ValueError("register needs a component or an explicit kind and name.")
    table = await self.table(subjects.PRESENCE_BUCKET, Registration, ttl_markers=True)
    presence = Presence(
      table,
      Registration(
        kind=kind,
        name=name,
        instance=self.instance,
        id=id or registration_id(),
        metadata=metadata or {},
      ),
      self.presence_ttl,
    )
    await presence.start()
    self._presences[id_of(presence)] = presence
    return presence

  async def unregister(self, presence: Presence) -> None:
    """Remove a presence entry made by `register` (it also expires by itself)."""
    self._presences.pop(id_of(presence), None)
    await presence.stop()

  def component_states(self) -> dict[str, ComponentState]:
    """The lifecycle `ComponentState` of each hosted component, by name."""
    return {component.name: component.phase for component in self._components}


def id_of(value: object) -> int:
  return id(value)
