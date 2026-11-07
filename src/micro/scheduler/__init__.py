"""Timers: do something at a time, and keep the promise across restarts.

    from micro.scheduler import Scheduler, Timers

    timers = Timers(runtime)                      # anywhere with a runtime
    await timers.event("reminder.42", REMIND, Reminder(user=1), after=3600)
    await timers.job("unban.7", UNBAN, Unban(user=7), at=datetime(2030, 1, 1, tzinfo=UTC))
    await timers.cancel("reminder.42")

    # and one `Scheduler()` component somewhere (any process group) delivers them.

A timer is a message the NATS server itself holds until its time (message scheduling,
NATS 2.12+), so it is durable, needs no polling, and is not tied to any one process.
At its time the server puts it on a "due" subject; a `Scheduler` publishes it as the
application event, or adds it to the work queue, it was made for, exactly as if the
timer's owner had done so then. If no `Scheduler` is running, timers that come due
wait and are delivered when one starts. A key names a timer: scheduling a key again
replaces it, and `cancel(key)` removes it. Times in the past fire at once.
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from nats.aio.msg import Msg
from nats.errors import NoRespondersError
from nats.js.api import RawStreamMsg, RetentionPolicy
from nats.js.errors import NotFoundError
from pydantic import JsonValue
from pydantic_core import from_json, to_json

from micro import subjects
from micro.runtime import Component, Retry, StreamConsumer

if TYPE_CHECKING:
  from micro.queue import WorkQueue
  from micro.runtime import Runtime
  from micro.service import EventSchema

SCHEDULE_HEADER = "Nats-Schedule"
TARGET_HEADER = "Nats-Schedule-Target"


@dataclass(frozen=True, slots=True)
class Timer:
  """A timer that has not fired yet."""

  key: str
  at: datetime
  kind: str
  """`event` or `job`."""
  target: str
  """The event id or work queue it will go to."""
  payload: JsonValue


async def ensure_stream(runtime: Runtime) -> None:
  """Create the scheduling stream (`MICRO_SCHEDULE`) if needed."""
  await runtime.ensure_stream(
    subjects.SCHEDULE_STREAM,
    subjects.SCHEDULE_SUBJECTS,
    retention=RetentionPolicy.LIMITS,
    allow_msg_schedules=True,
    max_msgs_per_subject=1,
  )
  info = await runtime.jetstream.stream_info(subjects.SCHEDULE_STREAM)
  if not info.config.allow_msg_schedules:
    raise RuntimeError("Timers need nats-server 2.12 or newer (message scheduling).")


def _when(at: datetime | float | None, after: timedelta | float | None) -> datetime:
  if (at is None) == (after is None):
    raise ValueError("Give exactly one of at= and after=.")
  if after is not None:
    seconds = after.total_seconds() if isinstance(after, timedelta) else float(after)
    return datetime.now(UTC) + timedelta(seconds=seconds)
  if isinstance(at, datetime):
    if at.tzinfo is None:
      raise ValueError("at= needs a timezone-aware datetime.")
    return at.astimezone(UTC)
  return datetime.fromtimestamp(float(at or 0), UTC)


class Timers:
  """Make, replace, cancel and list timers (needs a runtime, not a Scheduler)."""

  def __init__(self, runtime: Runtime) -> None:
    self.runtime = runtime
    self._ready = False

  async def _ensure(self) -> None:
    if not self._ready:
      await ensure_stream(self.runtime)
      self._ready = True

  async def _put(
    self,
    key: str,
    kind: str,
    target: str,
    payload: bytes,
    at: datetime | float | None,
    after: timedelta | float | None,
  ) -> datetime:
    await self._ensure()
    when = _when(at, after)
    body = to_json(
      {"key": key, "kind": kind, "target": target, "payload": from_json(payload)}
    )
    stamp = when.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    await self.runtime.jetstream.publish(
      subjects.schedule(key),
      body,
      stream=subjects.SCHEDULE_STREAM,
      headers={SCHEDULE_HEADER: f"@at {stamp}", TARGET_HEADER: subjects.due(key)},
    )
    return when

  async def event[T](
    self,
    key: str,
    event: EventSchema[T],
    payload: T,
    *,
    at: datetime | float | None = None,
    after: timedelta | float | None = None,
  ) -> datetime:
    """Publish `event` at a time (`at=` a datetime, or `after=` seconds). Returns when."""
    return await self._put(
      key, "event", event.id, event.encode_json(payload), at, after
    )

  async def job[T](
    self,
    key: str,
    queue: WorkQueue[T],
    job: T,
    *,
    at: datetime | float | None = None,
    after: timedelta | float | None = None,
  ) -> datetime:
    """Add a job to a work queue at a time."""
    await queue.ensure(self.runtime)
    return await self._put(key, "job", queue.name, queue.encode_json(job), at, after)

  async def cancel(self, key: str) -> bool:
    """Remove a timer that has not fired; False if there was none."""
    await self._ensure()
    subject = subjects.schedule(key)
    try:
      await self.runtime.jetstream.get_last_msg(subjects.SCHEDULE_STREAM, subject)
    except NotFoundError:
      return False
    await self.runtime.jetstream.purge_stream(subjects.SCHEDULE_STREAM, subject=subject)
    return True

  async def get(self, key: str) -> Timer | None:
    """The pending timer with this key, or None."""
    await self._ensure()
    try:
      message = await self.runtime.jetstream.get_last_msg(
        subjects.SCHEDULE_STREAM, subjects.schedule(key)
      )
    except NotFoundError:
      return None
    return _timer(message)

  async def pending(self, prefix: str = "") -> list[Timer]:
    """Timers not yet fired, soonest first (optionally only keys starting `prefix`)."""
    await self._ensure()
    js = self.runtime.jetstream
    info = await js.stream_info(
      subjects.SCHEDULE_STREAM, subjects_filter="micro.schedule.>"
    )
    found: list[Timer] = []
    for subject in sorted(info.state.subjects or {}):
      try:
        timer = _timer(await js.get_last_msg(subjects.SCHEDULE_STREAM, subject))
      except NotFoundError:
        continue  # it fired between the listing and the read
      if timer.key.startswith(prefix):
        found.append(timer)
    return sorted(found, key=lambda timer: timer.at)


def _timer(message: RawStreamMsg) -> Timer:
  body = from_json(message.data or b"{}")
  stamp = (message.headers or {})[SCHEDULE_HEADER].removeprefix("@at ").strip()
  return Timer(
    key=body["key"],
    at=datetime.fromisoformat(stamp),
    kind=body["kind"],
    target=body["target"],
    payload=body["payload"],
  )


class Scheduler(Component):
  """Delivers timers that come due. Run it once per deployment (replicas share the work).

  Add it to any process group: `components = ["micro.scheduler:Scheduler", ...]`.
  """

  kind = "scheduler"

  def __init__(self, name: str = "scheduler") -> None:
    super().__init__(name)
    self._consumer: StreamConsumer | None = None

  async def on_start(self) -> None:
    """Create the consumer for due timers."""
    await ensure_stream(self.runtime)
    self._consumer = StreamConsumer(
      self,
      stream=subjects.SCHEDULE_STREAM,
      durable=subjects.durable("sched", self.name),
      filters=["micro.due.>"],
      handler=self._deliver,
      concurrency=64,
      deliver_new=False,
    )
    await self._consumer.start()

  async def on_drain(self) -> None:
    """Stop taking due timers."""
    await self._stop()

  async def on_close(self) -> None:
    """Stop the consumer."""
    await self._stop()

  async def _stop(self) -> None:
    consumer, self._consumer = self._consumer, None
    if consumer is not None:
      await consumer.stop()

  async def _deliver(self, message: Msg) -> None:
    js = self.runtime.jetstream
    sequence = message.metadata.sequence.stream
    body = from_json(message.data)
    payload = to_json(body["payload"])
    if body["kind"] == "event":
      subject, stream = subjects.event(body["target"]), subjects.EVENTS_STREAM
    elif body["kind"] == "job":
      subject = subjects.work(body["target"])
      stream = subjects.work_stream(body["target"])
    else:
      raise ValueError(f"Unknown timer kind {body['kind']!r}.")
    try:
      # The stream sequence makes a redelivery publish the same message once.
      await js.publish(
        subject, payload, stream=stream, headers={"Nats-Msg-Id": f"timer-{sequence}"}
      )
    except NoRespondersError as error:
      raise Retry(5.0) from error
    await js.delete_msg(subjects.SCHEDULE_STREAM, sequence)


__all__ = ("Scheduler", "Timer", "Timers", "ensure_stream")
