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
    """The subject jobs are published on."""
    return subjects.work(self.name)

  @property
  def stream(self) -> str:
    """The JetStream stream that holds the jobs."""
    return subjects.work_stream(self.name)

  @property
  def durable(self) -> str:
    """The durable consumer name shared by all workers."""
    return subjects.durable("work", self.name)

  async def ensure(self, runtime: Runtime) -> None:
    """Create the queue's stream if it does not exist yet."""
    await runtime.ensure_stream(
      self.stream, (self.subject,), retention=RetentionPolicy.WORK_QUEUE
    )

  @property
  def hash(self) -> str:
    """Identifies the job schema; replicas compare it during rolling updates."""
    from micro.coordination import digest

    return digest(self._adapter.json_schema(mode="validation"))  # type: ignore[arg-type]

  def encode_json(self, value: T) -> bytes:
    """Encode a job as JSON."""
    return self._adapter.dump_json(self._adapter.validate_python(value))

  def decode_json(self, value: bytes) -> T:
    """Validate and decode a job."""
    return self._adapter.validate_json(value)
