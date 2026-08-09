from collections.abc import Sequence
from typing import Any

import nats
from nats.aio.client import Client
from nats.aio.msg import Msg
from nats.errors import TimeoutError
from nats.js.client import JetStreamContext
from nats.js.errors import BadRequestError, NotFoundError

from micro.gateway.event_service import GatewayEventDelivery


class JetStreamBackend:
  """NATS JetStream implementation of Micro's queue backend protocol."""

  def __init__(
    self,
    servers: Sequence[str] = ("nats://127.0.0.1:4222",),
    *,
    stream: str = "MICRO_QUEUE",
    subject_prefix: str = "micro.queue",
  ) -> None:
    self._servers = tuple(servers)
    self._stream = stream
    self._subject_prefix = subject_prefix
    self._connection: Client | None = None
    self._jetstream: JetStreamContext | None = None

  async def start(self) -> None:
    connection = await nats.connect(servers=list(self._servers))
    jetstream = connection.jetstream()
    try:
      await self._ensure_stream(jetstream)
    except BaseException:
      await connection.close()
      raise
    self._connection = connection
    self._jetstream = jetstream

  async def _ensure_stream(self, jetstream: JetStreamContext) -> None:
    subject = f"{self._subject_prefix}.>"
    try:
      info = await jetstream.stream_info(self._stream)
    except NotFoundError:
      try:
        info = await jetstream.add_stream(name=self._stream, subjects=[subject])
      except BadRequestError:
        # Another queue instance may have created the stream concurrently.
        info = await jetstream.stream_info(self._stream)
    if subject not in (info.config.subjects or []):
      raise RuntimeError(
        f"JetStream stream {self._stream!r} does not store subject {subject!r}."
      )

  async def publish(self, channel: str, payload: bytes) -> None:
    if self._jetstream is None:
      raise RuntimeError("The JetStream backend has not started.")
    await self._jetstream.publish(f"{self._subject_prefix}.{channel}", payload)

  async def close(self) -> None:
    if self._connection is None:
      return
    await self._connection.drain()
    self._connection = None
    self._jetstream = None


class _JetStreamDelivery(GatewayEventDelivery):
  def __init__(self, message: Msg) -> None:
    self._message = message

  @property
  def payload(self) -> bytes:
    return self._message.data

  async def acknowledge(self) -> None:
    await self._message.ack()

  async def retry(self) -> None:
    await self._message.nak()


class JetStreamGatewayEventSource:
  """Competing durable consumer for Micro's single gateway event channel."""

  def __init__(
    self,
    servers: Sequence[str] = ("nats://127.0.0.1:4222",),
    *,
    stream: str = "MICRO_QUEUE",
    durable: str = "micro-gateway-event-service",
    subject: str = "micro.queue.gateway.events",
  ) -> None:
    self._servers = tuple(servers)
    self._stream = stream
    self._durable = durable
    self._subject = subject
    self._connection: Client | None = None
    self._subscription: Any = None

  async def start(self) -> None:
    connection = await nats.connect(servers=list(self._servers))
    try:
      self._subscription = await connection.jetstream().pull_subscribe(
        self._subject,
        durable=self._durable,
        stream=self._stream,
      )
    except BaseException:
      await connection.close()
      raise
    self._connection = connection

  async def receive(self) -> GatewayEventDelivery:
    if self._subscription is None:
      raise RuntimeError("The JetStream event source has not started.")
    while True:
      try:
        messages = await self._subscription.fetch(batch=1, timeout=1)
      except TimeoutError:
        continue
      return _JetStreamDelivery(messages[0])

  async def close(self) -> None:
    if self._connection is None:
      return
    await self._connection.drain()
    self._connection = None
    self._subscription = None


__all__ = ("JetStreamBackend", "JetStreamGatewayEventSource")
