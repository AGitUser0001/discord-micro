import json
from typing import TYPE_CHECKING, Any

from nats.errors import NoRespondersError
from nats.errors import TimeoutError as NatsTimeoutError

from micro import subjects
from micro.errors import RemoteError, RequestTimeoutError, RoutingError
from micro.queue import WorkQueue

from ._event import DispatchSchema, EventSchema
from ._request import RequestSchema

if TYPE_CHECKING:
  from micro.runtime import Runtime

SCHEMA_HEADER = "Micro-Schema"
STATUS_HEADER = "Micro-Status"


class Client:
  """Calls requests, emits events, and enqueues work from anywhere in a deployment."""

  def __init__(self, runtime: Runtime, *, timeout: float = 5.0) -> None:
    if timeout <= 0:
      raise ValueError("timeout must be positive.")
    self.runtime = runtime
    self.timeout = timeout
    self._queues: set[str] = set()

  async def request[InputT, OutputT](
    self,
    request: RequestSchema[InputT, OutputT],
    payload: InputT,
    *,
    timeout: float | None = None,
  ) -> OutputT:
    """Call a request and return its typed reply. Raises `RemoteError`, `RoutingError` or `RequestTimeoutError`."""
    try:
      reply = await self.runtime.request(
        request.subject,
        request.encode_input_json(payload),
        timeout=timeout or self.timeout,
        headers={SCHEMA_HEADER: request.hash},
      )
    except NoRespondersError as exc:
      raise RoutingError(f"No service handles request {request.id!r}.") from exc
    except NatsTimeoutError as exc:
      raise RequestTimeoutError(f"Request {request.id!r} timed out.") from exc
    if reply.headers.get(STATUS_HEADER) == "error":
      raise remote_error(request.id, reply.data)
    return request.decode_output_json(reply.data)

  async def emit[T](self, event: EventSchema[T], payload: T) -> None:
    """Publish an event durably to every service listening for it.

    Services that are not listening when it is published do not receive it.
    """
    if isinstance(event, DispatchSchema):
      raise TypeError("Discord dispatches are published only by Gateway workers.")
    await self.runtime.jetstream.publish(
      event.subject, event.encode_json(payload), stream=subjects.EVENTS_STREAM
    )

  async def enqueue[T](self, queue: WorkQueue[T], job: T) -> None:
    """Add a job; it is kept until exactly one worker completes it."""
    if queue.name not in self._queues:
      await queue.ensure(self.runtime)
      self._queues.add(queue.name)
    await self.runtime.jetstream.publish(
      queue.subject, queue.encode_json(job), stream=queue.stream
    )


def error_body(code: str, message: str, detail: Any = None) -> bytes:
  return json.dumps({"code": code, "message": message, "detail": detail}).encode()


def remote_error(target: str, body: bytes) -> RemoteError:
  try:
    decoded = json.loads(body)
  except ValueError:
    decoded = None
  if not isinstance(decoded, dict):
    return RemoteError(target, "invalid_reply", body.decode(errors="replace"))
  return RemoteError(
    target,
    str(decoded.get("code", "unknown")),
    str(decoded.get("message", "")),
    detail=decoded.get("detail"),
  )
