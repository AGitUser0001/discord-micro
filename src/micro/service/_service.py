import asyncio
import inspect
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from re import fullmatch
from typing import TYPE_CHECKING, Any

from nats.aio.msg import Msg
from nats.aio.subscription import Subscription
from pydantic import JsonValue, ValidationError

from micro import subjects
from micro.errors import ServiceError
from micro.queue import WorkQueue
from micro.runtime import Component, Presence, Reject, Retry, StreamConsumer

from ._client import SCHEMA_HEADER, STATUS_HEADER, Client, error_body
from ._event import EventSchema
from ._request import RequestSchema

if TYPE_CHECKING:
  from micro.store import GraphModule

logger = logging.getLogger("micro")

type EventHandler[T] = Callable[[T], Awaitable[None]]
type RequestHandler[InputT, OutputT] = Callable[[InputT], Awaitable[OutputT]]
type EventPredicate[T] = Callable[[T], bool]

_SERVICE_NAME_PATTERN = r"[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?"


class DuplicateRequestHandlerError(ValueError):
  pass


class DuplicateWorkHandlerError(ValueError):
  pass


@dataclass(frozen=True, slots=True)
class _Listener:
  event: EventSchema[Any]
  handler: EventHandler[Any]
  guild_id: int | None
  when: EventPredicate[Any] | None

  @property
  def label(self) -> str:
    return f"{self.handler.__module__}:{self.handler.__qualname__}"


class Service(Component):
  """An application microservice with typed requests, events, and work.

  * `@service.handle(request)`: one replica of one service answers each call.
  * `@service.listen(event)`: every listening service receives each event once,
    load-balanced across its replicas; a service may have many listeners.
  * `@service.work(queue)`: each job goes to exactly one worker.

  Replicas share the service name. Start more to scale; drain old ones to roll.
  """

  kind = "service"

  def __init__(
    self,
    name: str,
    *,
    version: str = "0",
    concurrency: int = 64,
  ) -> None:
    if fullmatch(_SERVICE_NAME_PATTERN, name) is None:
      raise ValueError(
        "Service names must contain only letters, numbers, dots, underscores, and "
        "hyphens, and must start and end with a letter or number."
      )
    if concurrency <= 0:
      raise ValueError("concurrency must be positive.")
    super().__init__(name)
    self.version = version
    self.concurrency = concurrency
    self._listeners: list[_Listener] = []
    self._requests: dict[
      str, tuple[RequestSchema[Any, Any], RequestHandler[Any, Any]]
    ] = {}
    self._work: dict[str, tuple[WorkQueue[Any], EventHandler[Any]]] = {}
    self._modules: dict[str, GraphModule] = {}
    self._client: Client | None = None
    self._subscriptions: list[Subscription] = []
    self._consumers: list[StreamConsumer] = []
    self._request_slots = asyncio.Semaphore(concurrency)
    self._presence: Presence | None = None

  # Declaration -----------------------------------------------------------------

  def listen[T](
    self,
    event: EventSchema[T],
    *,
    guild_id: int | None = None,
    when: EventPredicate[T] | None = None,
  ) -> Callable[[EventHandler[T]], EventHandler[T]]:
    """Register an event handler.

    `guild_id` narrows Discord dispatches on the server; `when` filters in-process.
    """
    event.listen_subject(guild_id=guild_id)

    def register(handler: EventHandler[T]) -> EventHandler[T]:
      self._declaring("Event handlers")
      _require_async(handler, "Event handlers")
      self._listeners.append(_Listener(event, handler, guild_id, when))
      return handler

    return register

  def handle[InputT, OutputT](
    self,
    request: RequestSchema[InputT, OutputT],
  ) -> Callable[[RequestHandler[InputT, OutputT]], RequestHandler[InputT, OutputT]]:
    def register(
      handler: RequestHandler[InputT, OutputT],
    ) -> RequestHandler[InputT, OutputT]:
      self._declaring("Request handlers")
      if request.id in self._requests:
        raise DuplicateRequestHandlerError(
          f"This service already handles request {request.id!r}."
        )
      _require_async(handler, "Request handlers")
      self._requests[request.id] = (request, handler)
      return handler

    return register

  def work[T](
    self, queue: WorkQueue[T]
  ) -> Callable[[EventHandler[T]], EventHandler[T]]:
    def register(handler: EventHandler[T]) -> EventHandler[T]:
      self._declaring("Work handlers")
      if queue.name in self._work:
        raise DuplicateWorkHandlerError(
          f"This service already works queue {queue.name!r}."
        )
      _require_async(handler, "Work handlers")
      self._work[queue.name] = (queue, handler)
      return handler

    return register

  def uses(self, *modules: GraphModule) -> None:
    """Declare graph modules a running store must serve for this service."""
    self._declaring("Graph modules")
    for module in modules:
      self._modules[module.id] = module

  def _declaring(self, what: str) -> None:
    if self.state.value != "created":
      raise RuntimeError(f"{what} cannot be added after the service starts.")

  # Introspection ---------------------------------------------------------------

  @property
  def client(self) -> Client:
    if self._client is None:
      raise RuntimeError(f"Service {self.name!r} has not started.")
    return self._client

  def metadata(self) -> dict[str, JsonValue]:
    """What this service advertises in the presence table."""
    requests: dict[str, JsonValue] = {
      request_id: schema.hash
      for request_id, (schema, _) in sorted(self._requests.items())
    }
    events: list[JsonValue] = [
      *sorted({listener.event.id for listener in self._listeners})
    ]
    work: list[JsonValue] = [*sorted(self._work)]
    modules: list[JsonValue] = [
      {"id": module.id, "schema": module.graphql_schema}
      for module in sorted(self._modules.values(), key=lambda item: item.id)
    ]
    metadata: dict[str, JsonValue] = {
      "version": self.version,
      "requests": requests,
      "events": events,
      "work": work,
      "modules": modules,
    }
    return metadata

  # Lifecycle -------------------------------------------------------------------

  async def on_start(self) -> None:
    runtime = self.runtime
    self._client = Client(runtime)
    for request_id, (schema, handler) in self._requests.items():
      self._subscriptions.append(
        await runtime.nats.subscribe(
          schema.subject,
          queue=request_id,
          cb=self._request_callback(schema, handler),
        )
      )
    if self._listeners:
      consumer = StreamConsumer(
        self,
        stream=subjects.EVENTS_STREAM,
        durable=subjects.durable("svc", self.name),
        filters=[
          listener.event.listen_subject(guild_id=listener.guild_id)
          for listener in self._listeners
        ],
        handler=self._dispatch_event,
        concurrency=self.concurrency,
      )
      await consumer.start()
      self._consumers.append(consumer)
    for queue, handler in self._work.values():
      await queue.ensure(runtime)
      consumer = StreamConsumer(
        self,
        stream=queue.stream,
        durable=queue.durable,
        filters=[queue.subject],
        handler=self._work_callback(queue, handler),
        concurrency=self.concurrency,
        deliver_new=False,
      )
      await consumer.start()
      self._consumers.append(consumer)
    self._presence = await runtime.register(self, metadata=self.metadata())
    self._report_conflicts()

  async def on_drain(self) -> None:
    await self._stop_sources()

  async def on_close(self) -> None:
    await self._stop_sources()

  async def _stop_sources(self) -> None:
    if self._presence is not None:
      await self.runtime.unregister(self._presence)
      self._presence = None
    subscriptions, self._subscriptions = self._subscriptions, []
    for subscription in subscriptions:
      try:
        await subscription.drain()
      except Exception:
        logger.debug("Subscription drain failed", exc_info=True)
    consumers, self._consumers = self._consumers, []
    await asyncio.gather(*(consumer.stop() for consumer in consumers))

  def _report_conflicts(self) -> None:
    mine = set(self._requests)
    for entry in self.runtime.directory.entries("service"):
      if entry.name == self.name:
        continue
      theirs = entry.metadata.get("requests")
      if isinstance(theirs, dict) and (overlap := mine & set(theirs)):
        logger.error(
          "Services %r and %r both handle %s; calls are split between them.",
          self.name,
          entry.name,
          ", ".join(sorted(overlap)),
        )

  # Wire handling ---------------------------------------------------------------

  def _request_callback[InputT, OutputT](
    self,
    schema: RequestSchema[InputT, OutputT],
    handler: RequestHandler[InputT, OutputT],
  ) -> Callable[[Msg], Awaitable[None]]:
    async def callback(message: Msg) -> None:
      await self._request_slots.acquire()
      task = asyncio.create_task(self._answer(message, schema, handler))
      task.add_done_callback(lambda _: self._request_slots.release())

    return callback

  async def _answer[InputT, OutputT](
    self,
    message: Msg,
    schema: RequestSchema[InputT, OutputT],
    handler: RequestHandler[InputT, OutputT],
  ) -> None:
    async with self.tracked():
      try:
        body = await self._run_request(message, schema, handler)
        headers = {STATUS_HEADER: "ok"}
      except ServiceError as exc:
        body = error_body(exc.code, exc.message, exc.detail)
        headers = {STATUS_HEADER: "error"}
      if message.reply:
        await self.runtime.nats.publish(message.reply, body, headers=headers)

  async def _run_request[InputT, OutputT](
    self,
    message: Msg,
    schema: RequestSchema[InputT, OutputT],
    handler: RequestHandler[InputT, OutputT],
  ) -> bytes:
    expected = (message.headers or {}).get(SCHEMA_HEADER)
    if expected is not None and expected != schema.hash:
      raise ServiceError(
        "incompatible_schema",
        f"Caller and handler disagree on request {schema.id!r}.",
        detail={"caller": expected, "handler": schema.hash},
      )
    try:
      payload = schema.decode_input_json(message.data)
    except ValidationError as exc:
      raise ServiceError(
        "invalid_input",
        f"Input does not match request {schema.id!r}.",
        detail=_errors(exc),
      ) from exc
    try:
      result = await handler(payload)
    except ServiceError:
      raise
    except Exception as exc:
      logger.exception("Request handler for %s failed", schema.id)
      raise ServiceError("handler_failed", f"{type(exc).__name__}: {exc}") from exc
    try:
      return schema.encode_output_json(result)
    except ValidationError as exc:
      raise ServiceError(
        "invalid_output",
        f"Handler output does not match request {schema.id!r}.",
        detail=_errors(exc),
      ) from exc

  async def _dispatch_event(self, message: Msg) -> None:
    matching = [
      listener
      for listener in self._listeners
      if listener.event.matches(message.subject)
    ]
    if not matching:
      # A newer replica updated the shared consumer; let it take this event.
      raise Retry(1.0)
    guild = _guild_of(message.subject)
    decoded: dict[str, Any] = {}
    runs: list[tuple[_Listener, Awaitable[None]]] = []
    for listener in matching:
      if listener.guild_id is not None and guild != listener.guild_id:
        continue
      event = listener.event
      if event.id not in decoded:
        try:
          decoded[event.id] = event.decode_json(message.data)
        except ValidationError as exc:
          logger.error("Event %s does not match its schema: %s", event.id, exc)
          raise Reject from exc
      payload = decoded[event.id]
      if listener.when is not None and not listener.when(payload):
        continue
      runs.append((listener, listener.handler(payload)))
    results = await asyncio.gather(*(run for _, run in runs), return_exceptions=True)
    failures = [
      (listener, result)
      for (listener, _), result in zip(runs, results)
      if isinstance(result, BaseException)
    ]
    for listener, error in failures:
      logger.error(
        "Handler %s failed for event %s",
        listener.label,
        listener.event.id,
        exc_info=error,
      )
    if failures:
      raise Retry(min(2.0 ** ((message.metadata.num_delivered or 1) - 1), 60.0))

  def _work_callback[T](
    self, queue: WorkQueue[T], handler: EventHandler[T]
  ) -> Callable[[Msg], Awaitable[None]]:
    async def callback(message: Msg) -> None:
      try:
        job = queue.decode_json(message.data)
      except ValidationError as exc:
        logger.error("Job in %s does not match its schema: %s", queue.name, exc)
        raise Reject from exc
      await handler(job)

    return callback


def _guild_of(subject: str) -> int | None:
  last = subject.rsplit(".", 1)[-1]
  return int(last) if last.isdecimal() else None


def _errors(exc: ValidationError) -> JsonValue:
  return [
    {"path": [str(part) for part in error["loc"]], "message": error["msg"]}
    for error in exc.errors(include_url=False)
  ]


def _require_async(handler: Callable[..., Any], what: str) -> None:
  if not inspect.iscoroutinefunction(handler):
    raise TypeError(f"{what} must be async functions.")
