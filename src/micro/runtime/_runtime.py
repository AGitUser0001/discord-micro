import asyncio
import logging
import os
import signal
import socket
from collections.abc import Sequence
from contextlib import suppress
from dataclasses import dataclass
from types import TracebackType
from typing import Any, Self
from uuid import uuid4

import nats
from nats.aio.client import Client as NATS
from nats.js.api import RetentionPolicy, StorageType, StreamConfig
from nats.js.client import JetStreamContext
from nats.js.errors import BadRequestError
from pydantic import JsonValue

from micro import subjects
from micro.coordination import LockHolder, Locks, Table

from ._component import Component, ComponentState
from ._presence import Directory, Presence, Registration, registration_id

logger = logging.getLogger("micro")

DEFAULT_NATS_URL = "nats://127.0.0.1:4222"
RUNTIME_KIND = "runtime"
PAYLOAD_HEADER = "Micro-Payload"
"""Names the object holding a request or reply body too large for one message."""
PAYLOAD_TTL = 3600.0
"""Seconds an unread large payload is kept (readers delete them immediately)."""
_HEADROOM = 64 * 1024


@dataclass(frozen=True, slots=True)
class Reply:
  data: bytes
  headers: dict[str, str]


def default_servers() -> tuple[str, ...]:
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
    self._payloads: Any = None

  @property
  def nats(self) -> NATS:
    if self._nats is None:
      raise RuntimeError("Runtime has not started.")
    return self._nats

  @property
  def jetstream(self) -> JetStreamContext:
    if self._jetstream is None:
      raise RuntimeError("Runtime has not started.")
    return self._jetstream

  @property
  def directory(self) -> Directory:
    if self._directory is None:
      raise RuntimeError("Runtime has not started.")
    return self._directory

  @property
  def components(self) -> tuple[Component, ...]:
    return tuple(self._components)

  @property
  def ready(self) -> bool:
    return (
      self._started
      and self._nats is not None
      and self._nats.is_connected
      and all(component.ready for component in self._components)
    )

  async def start(self) -> None:
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
        logger.exception("Draining %s failed", component.name)

  async def close(self) -> None:
    for component in reversed(self._components):
      try:
        await component.close()
      except Exception:
        logger.exception("Closing %s failed", component.name)
    self._components.clear()
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
      logger.info(
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
    self, message: Any, body: bytes, *, headers: dict[str, str] | None = None
  ) -> None:
    """Reply to a request (any size); does nothing for messages without a reply."""
    if message.reply:
      data, sent = await self._encode(body, headers)
      await self.nats.publish(message.reply, data, headers=sent)

  async def payload(self, message: Any) -> bytes:
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

  async def _payload_store(self) -> Any:
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

  async def locks(self) -> Locks:
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
    self._presences.pop(id_of(presence), None)
    await presence.stop()

  def component_states(self) -> dict[str, ComponentState]:
    return {component.name: component.phase for component in self._components}


def id_of(value: object) -> int:
  return id(value)
