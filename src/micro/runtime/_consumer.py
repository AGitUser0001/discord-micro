import asyncio
import logging
from collections.abc import Awaitable, Callable, Sequence
from contextlib import suppress
from typing import TYPE_CHECKING

from nats.aio.msg import Msg
from nats.errors import TimeoutError as NatsTimeoutError
from nats.js.api import AckPolicy, ConsumerConfig, DeliverPolicy

from micro.errors import DrainingError

if TYPE_CHECKING:
  from ._component import Component

logger = logging.getLogger("micro")

_FETCH_WAIT = 5.0
"""How long one pull waits for messages before the loop re-checks draining."""


class Retry(Exception):
  """Raise from a stream handler to have the message redelivered later."""

  def __init__(self, delay: float = 0.0) -> None:
    self.delay = delay
    super().__init__(f"retry after {delay}s")


class Reject(Exception):
  """Raise from a stream handler when redelivery can never succeed."""


type StreamHandler = Callable[[Msg], Awaitable[None]]


def default_backoff(deliveries: int) -> float:
  """Delay before redelivering a message that failed `deliveries` times."""
  return float(min(2 ** (deliveries - 1), 60))


class StreamConsumer:
  """One durable consumer shared by every replica of a logical component.

  Each message is delivered to one replica. A handler that returns acknowledges
  it; `Retry` or an unexpected exception redelivers it (at least once); `Reject`
  terminates it. Long handlers keep their message alive with progress acks, so
  there is no handler deadline.
  """

  def __init__(
    self,
    component: Component,
    *,
    stream: str,
    durable: str,
    filters: Sequence[str],
    handler: StreamHandler,
    concurrency: int = 64,
    ack_wait: float = 30.0,
    deliver_new: bool = True,
    backoff: Callable[[int], float] = default_backoff,
    ack_first: bool = False,
  ) -> None:
    if concurrency <= 0:
      raise ValueError("concurrency must be positive.")
    if not filters:
      raise ValueError("A stream consumer needs at least one filter subject.")
    self._component = component
    self.stream = stream
    self.durable = durable
    self.filters = tuple(sorted(set(filters)))
    self._handler = handler
    self._slots = asyncio.Semaphore(concurrency)
    self._concurrency = concurrency
    self._ack_wait = ack_wait
    self._deliver_new = deliver_new
    self._backoff = backoff
    self._ack_first = ack_first
    self._loop: asyncio.Task[None] | None = None
    self._handlers: set[asyncio.Task[None]] = set()

  async def start(self) -> None:
    js = self._component.runtime.jetstream
    config = ConsumerConfig(
      durable_name=self.durable,
      ack_policy=AckPolicy.EXPLICIT,
      ack_wait=self._ack_wait,
      deliver_policy=DeliverPolicy.NEW if self._deliver_new else DeliverPolicy.ALL,
      max_ack_pending=-1,
      max_deliver=-1,
    )
    if len(self.filters) == 1:
      config.filter_subject = self.filters[0]
    else:
      config.filter_subjects = list(self.filters)
    await js.add_consumer(self.stream, config)
    subscription = await js.pull_subscribe_bind(self.durable, self.stream)
    self._loop = self._component.spawn(
      self._consume(subscription), name=f"consumer.{self.durable}"
    )

  async def stop(self) -> None:
    """Stop fetching, then wait for handlers already running."""
    if self._loop is not None:
      self._loop.cancel()
      with suppress(asyncio.CancelledError):
        await self._loop
      self._loop = None
    if self._handlers:
      await asyncio.gather(*tuple(self._handlers), return_exceptions=True)

  async def _consume(self, subscription: object) -> None:
    from nats.js.client import JetStreamContext

    assert isinstance(subscription, JetStreamContext.PullSubscription)
    try:
      while self._component.active:
        await self._slots.acquire()
        free = 1
        while free < self._concurrency and not self._slots.locked():
          await self._slots.acquire()
          free += 1
        try:
          messages = await subscription.fetch(free, timeout=_FETCH_WAIT)
        except NatsTimeoutError:
          messages = []
        except asyncio.CancelledError:
          for _ in range(free):
            self._slots.release()
          raise
        except Exception:
          logger.warning("Fetch from %s failed", self.durable, exc_info=True)
          messages = []
          await asyncio.sleep(1)
        for _ in range(free - len(messages)):
          self._slots.release()
        for message in messages:
          task = asyncio.create_task(self._handle(message))
          self._handlers.add(task)
          task.add_done_callback(self._handlers.discard)
    finally:
      with suppress(Exception):
        await subscription.unsubscribe()

  async def _handle(self, message: Msg) -> None:
    if self._ack_first:
      await self._handle_acknowledged(message)
      return
    keepalive = asyncio.create_task(self._keepalive(message))
    try:
      async with self._component.tracked():
        await self._handler(message)
    except DrainingError:
      await _settle(message.nak())
    except Retry as retry:
      await _settle(message.nak(delay=retry.delay or None))
    except Reject:
      logger.warning("Rejected %s from %s", message.subject, self.durable)
      await _settle(message.term())
    except Exception:
      deliveries = message.metadata.num_delivered or 1
      logger.exception(
        "Handler for %s in %s failed (delivery %d)",
        message.subject,
        self.durable,
        deliveries,
      )
      await _settle(message.nak(delay=self._backoff(deliveries)))
    else:
      await _settle(message.ack())
    finally:
      keepalive.cancel()
      self._slots.release()

  async def _handle_acknowledged(self, message: Msg) -> None:
    """At-most-once: acknowledge first, so a failure is never redelivered."""
    try:
      await _settle(message.ack())
      async with self._component.tracked():
        await self._handler(message)
    except Exception:
      logger.exception("Handler for %s in %s failed", message.subject, self.durable)
    finally:
      self._slots.release()

  async def _keepalive(self, message: Msg) -> None:
    while True:
      await asyncio.sleep(self._ack_wait / 2)
      with suppress(Exception):
        await message.in_progress()


async def _settle(operation: Awaitable[object]) -> None:
  try:
    await operation
  except Exception:
    logger.warning("Could not settle a stream message", exc_info=True)
