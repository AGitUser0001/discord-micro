import asyncio
from collections.abc import Sequence
from typing import Any

import nats
from nats.aio.client import Client
from nats.errors import TimeoutError
from nats.js.api import ConsumerConfig
from nats.js.client import JetStreamContext
from nats.js.errors import BadRequestError, NotFoundError

from micro.queue import QueueBackendDelivery, QueueObservation

_REPLY_HEADER = "Micro-Reply"


class JetStreamBackend:
  """NATS JetStream implementation of Micro's queue backend protocol."""

  def __init__(
    self,
    servers: Sequence[str] = ("nats://127.0.0.1:4222",),
    *,
    stream: str = "MICRO_QUEUE",
    subject_prefix: str = "micro.queue",
    acknowledgement_deadline: float = 30.0,
    max_deliveries: int = 10,
  ) -> None:
    if acknowledgement_deadline <= 0 or max_deliveries <= 0:
      raise ValueError("JetStream delivery limits must be positive.")
    self._servers = tuple(servers)
    self._stream = stream
    self._subject_prefix = subject_prefix
    self._acknowledgement_deadline = acknowledgement_deadline
    self._max_deliveries = max_deliveries
    self._connection: Client | None = None
    self._jetstream: JetStreamContext | None = None
    self._subscriptions: dict[tuple[str, str], Any] = {}
    self._subscription_lock = asyncio.Lock()

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

  async def request(
    self,
    channel: str,
    payload: bytes,
    *,
    timeout: float,
  ) -> bytes:
    if self._connection is None or self._jetstream is None:
      raise RuntimeError("The JetStream backend has not started.")
    inbox = self._connection.new_inbox()
    subscription = await self._connection.subscribe(inbox, max_msgs=1)
    try:
      await self._jetstream.publish(
        f"{self._subject_prefix}.{channel}",
        payload,
        headers={_REPLY_HEADER: inbox},
      )
      try:
        response = await subscription.next_msg(timeout=timeout)
      except TimeoutError as exc:
        raise TimeoutError from exc
      return response.data
    finally:
      await subscription.unsubscribe()

  async def consume(
    self,
    channel: str,
    consumer: str,
    *,
    timeout: float,
  ) -> QueueBackendDelivery | None:
    if self._connection is None or self._jetstream is None:
      raise RuntimeError("The JetStream backend has not started.")
    key = (channel, consumer)
    subscription = self._subscriptions.get(key)
    if subscription is None:
      async with self._subscription_lock:
        subscription = self._subscriptions.get(key)
        if subscription is None:
          subscription = await self._jetstream.pull_subscribe(
            f"{self._subject_prefix}.{channel}",
            durable=consumer,
            stream=self._stream,
            config=ConsumerConfig(
              durable_name=consumer,
              ack_wait=self._acknowledgement_deadline,
              max_deliver=self._max_deliveries,
            ),
          )
          self._subscriptions[key] = subscription
    try:
      messages = await subscription.fetch(batch=1, timeout=timeout)
    except TimeoutError:
      return None
    message = messages[0]
    return QueueBackendDelivery(
      message.data,
      message.reply,
      message.headers.get(_REPLY_HEADER) if message.headers else None,
    )

  async def acknowledge(self, receipt: str) -> None:
    await self._settle(receipt)

  async def retry(self, receipt: str, *, delay: float = 0) -> None:
    payload = (
      b"-NAK"
      if delay == 0
      else f'-NAK {{"delay":{int(delay * 1_000_000_000)}}}'.encode()
    )
    await self._settle(receipt, payload)

  async def dead_letter(self, receipt: str) -> None:
    await self._settle(receipt, b"+TERM")

  async def respond(self, receipt: str, reply: str, payload: bytes) -> None:
    if self._connection is None:
      raise RuntimeError("The JetStream backend has not started.")
    await self._connection.publish(reply, payload)
    await self._connection.flush()
    await self._settle(receipt)

  async def _settle(self, receipt: str, payload: bytes = b"") -> None:
    if self._connection is None:
      raise RuntimeError("The JetStream backend has not started.")
    await self._connection.publish(receipt, payload)
    await self._connection.flush()

  async def close(self) -> None:
    if self._connection is None:
      return
    await self._connection.drain()
    self._connection = None
    self._jetstream = None
    self._subscriptions.clear()

  async def observe(self) -> QueueObservation:
    if self._jetstream is None:
      return QueueObservation(False)
    info = await self._jetstream.stream_info(self._stream)
    return QueueObservation(
      True,
      pending=info.state.messages,
      consumers=info.state.consumer_count,
    )


__all__ = ("JetStreamBackend",)
