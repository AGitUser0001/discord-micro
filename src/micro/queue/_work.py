from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from nats.js.api import RetentionPolicy
from pydantic import TypeAdapter

from micro import subjects

if TYPE_CHECKING:
  from micro.runtime import Runtime


@dataclass(frozen=True, slots=True)
class WorkQueue[T]:
  """A durable queue of typed jobs.

  Jobs are kept until a worker finishes them, even when no worker is running
  yet. Each job goes to exactly one worker across every service and replica;
  failed jobs are retried. Declare it once and share it between producers
  (`Client.enqueue`) and workers (`Service.work`).
  """

  name: str
  payload: Any
  _adapter: TypeAdapter[T] = field(init=False, repr=False, compare=False)

  def __post_init__(self) -> None:
    subjects.dotted(self.name)
    object.__setattr__(self, "_adapter", TypeAdapter[T](self.payload))

  @property
  def subject(self) -> str:
    return subjects.work(self.name)

  @property
  def stream(self) -> str:
    return subjects.work_stream(self.name)

  @property
  def durable(self) -> str:
    return subjects.durable("work", self.name)

  async def ensure(self, runtime: Runtime) -> None:
    await runtime.ensure_stream(
      self.stream, (self.subject,), retention=RetentionPolicy.WORK_QUEUE
    )

  def encode_json(self, value: T) -> bytes:
    return self._adapter.dump_json(self._adapter.validate_python(value))

  def decode_json(self, value: bytes) -> T:
    return self._adapter.validate_json(value)
