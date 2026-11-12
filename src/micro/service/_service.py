import asyncio
import inspect
from collections.abc import Awaitable, Callable
from contextlib import suppress
from dataclasses import dataclass
from re import fullmatch
from re import sub as re_sub
from typing import TYPE_CHECKING, Any, Literal, Never, Protocol, overload

from nats.aio.msg import Msg
from nats.aio.subscription import Subscription
from pydantic import JsonValue, ValidationError

from micro import log, subjects
from micro._handling import handling
from micro.coordination import DECLARATIONS_KEY, Declarations, LockLost
from micro.errors import ServiceError
from micro.middleware import Middleware, Middlewares
from micro.queue import WorkQueue
from micro.runtime import Component, Presence, Reject, Retry, StreamConsumer

from ._call import UNSET, Call
from ._client import SCHEMA_HEADER, STATUS_HEADER, Client, error_body
from ._event import EventSchema
from ._inject import NO_PAYLOAD, call_handler
from ._request import RequestSchema

if TYPE_CHECKING:
  from micro.discord.interactions import Context
  from micro.store import GraphModule

type _Done = Awaitable[None]
type EventHandler[T] = Callable[["Context", T], _Done]
"""An event or work handler: `async def f(ctx: Context, event: T)`. For a Discord event `T`
is the object it is about (`Message`, `Member`, ...), bound to `ctx`; `event.before` is the
object as it was when the event changed one."""
type RequestHandler[InputT, OutputT] = Callable[[InputT], Awaitable[OutputT]]
type EventPredicate[T] = Callable[[T], bool]
type PeriodicHandler = Callable[["Context"], _Done]
"""A handler `every`, `startup` and `shutdown` run: `async def f(ctx: Context)`."""

_SERVICE_NAME_PATTERN = r"[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?"


class DuplicateRequestHandlerError(ValueError):
  pass


class DuplicateWorkHandlerError(ValueError):
  pass


class ServiceExtension(Protocol):
  """A template that adds behavior to a service (commands, components, ...).

  Extensions start after the service's own sources and before it registers in
  presence; their metadata is advertised with the service's.
  """

  async def start(self, service: Service) -> None: ...

  async def stop(self) -> None: ...

  def metadata(self) -> dict[str, JsonValue]: ...


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
    ordered_by_guild: bool = False,
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
    self._periodic: list[tuple[PeriodicHandler, float]] = []
    self._startup: list[PeriodicHandler] = []
    self._shutdown: list[PeriodicHandler] = []
    self._requests: dict[
      str, tuple[RequestSchema[Any, Any], RequestHandler[Any, Any]]
    ] = {}
    self._work: dict[str, tuple[WorkQueue[Any], EventHandler[Any]]] = {}
    self._declarations: dict[str, dict[str, JsonValue]] = {}
    self._declared: dict[str, dict[str, str]] = {}
    self._extensions: list[ServiceExtension] = []
    self._call_middleware: Middlewares[Call] = Middlewares()
    self._client: Client | None = None
    self._subscriptions: list[Subscription] = []
    self._consumers: list[StreamConsumer] = []
    self._request_slots = asyncio.Semaphore(concurrency)
    self._presence: Presence | None = None
    self.ordered_by_guild = ordered_by_guild
    self._guild_locks: dict[int | None, asyncio.Lock] = {}
    self._succeeded: dict[int, set[int]] = {}

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

  def startup(self, handler: PeriodicHandler) -> PeriodicHandler:
    """Run a handler once when the service starts, before it takes any work: open a
    connection, warm a cache.

        @service.startup
        async def setup(ctx: Context) -> None: ...
    """
    self._declaring("Startup handlers")
    _require_async(handler, "Startup handlers")
    self._startup.append(handler)
    return handler

  def shutdown(self, handler: PeriodicHandler) -> PeriodicHandler:
    """Run a handler once when the service closes, after its work has finished: release
    what `startup` opened. A handler that raises is logged and the rest still run."""
    self._declaring("Shutdown handlers")
    _require_async(handler, "Shutdown handlers")
    self._shutdown.append(handler)
    return handler

  def every(
    self, seconds: float = 0, *, minutes: float = 0, hours: float = 0
  ) -> Callable[[PeriodicHandler], PeriodicHandler]:
    """Run a handler again and again: `@service.every(minutes=5)`.

    It runs once at start and then again an interval after each run ends, on **one replica
    at a time** (the others wait, and one takes over if it goes away), so a job that
    must happen once is not done once per replica. A run that raises is logged and the
    next one still happens; one that takes longer than the interval just delays the next.

    Args:
      seconds: The interval in seconds.
      minutes: Added to it, in minutes.
      hours: Added to it, in hours.

    Raises:
      ValueError: The total interval is not positive.
    """
    total = seconds + minutes * 60 + hours * 3600
    if total <= 0:
      raise ValueError("every() needs a positive interval.")

    def register(handler: PeriodicHandler) -> PeriodicHandler:
      self._declaring("Periodic tasks")
      _require_async(handler, "Periodic tasks")
      self._periodic.append((handler, total))
      return handler

    return register

  def handle[InputT, OutputT](
    self,
    request: RequestSchema[InputT, OutputT],
  ) -> Callable[[RequestHandler[InputT, OutputT]], RequestHandler[InputT, OutputT]]:
    """Register the handler for a request schema. Exactly one replica answers each call."""

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
    """Register a worker for a queue. Each job goes to exactly one worker."""

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

  @overload
  def use(self, scope: Middleware, /) -> Middleware: ...
  @overload
  def use(self, scope: str, function: Middleware, /) -> Middleware: ...
  @overload
  def use(self, scope: str, /) -> Callable[[Middleware], Middleware]: ...

  def use(
    self, scope: Middleware | str, function: Middleware | None = None, /
  ) -> Middleware | Callable[[Middleware], Middleware]:
    """Add middleware around every request, event and job handler.

    `fn(call, next[, end])`; see `Call`. `use("scope", fn)` limits it to a
    request ID, event ID or queue name, and the dotted names under it.
    """
    self._declaring("Middleware")
    if function is None:
      return self._call_middleware.use(scope)  # pyright: ignore[reportCallIssue, reportArgumentType]
    return self._call_middleware.use(scope, function)  # pyright: ignore[reportArgumentType]

  def uses(self, *modules: GraphModule) -> None:
    """Declare graph modules a running store must serve for this service."""
    for module in modules:
      self.declare(
        "modules", module.id, {"id": module.id, "schema": module.graphql_schema}
      )

  def declare(self, kind: str, key: str, document: JsonValue) -> None:
    """Declare a versioned document (a command, a graph module, ...).

    Declarations converge: consumers apply a new version only when every live
    replica declaring the key agrees on it (see `micro.coordination.Declarations`).
    """
    if self.phase.value not in ("created", "starting"):
      raise RuntimeError("Declarations cannot be added after the service starts.")
    self._declarations.setdefault(subjects.token(kind), {})[key] = document

  def extend(self, extension: ServiceExtension) -> None:
    """Attach a template such as `Commands(service)` (they call this themselves)."""
    self._declaring("Extensions")
    self._extensions.append(extension)

  async def _run_every(
    self, handler: PeriodicHandler, interval: float, label: str
  ) -> None:
    """Run a periodic handler while this replica holds its lock (one replica at a time)."""
    locks = await self.runtime.locks()
    key = "every." + re_sub(r"[^A-Za-z0-9_-]+", "_", f"{self.name}.{label}")
    while self.active:
      try:
        async with locks.hold(key, ttl=30) as lease:
          while self.active and not lease.lost.is_set():
            try:
              async with self.tracked():
                with handling(self.name, f"every {label}"):
                  await call_handler(self, handler, NO_PAYLOAD)
            except Exception:
              log.exception("A periodic task failed", task=label)
            with suppress(TimeoutError):
              await asyncio.wait_for(lease.lost.wait(), timeout=interval)
      except LockLost:
        log.warning("A periodic task lost its lock; waiting for it again", task=label)

  def _declaring(self, what: str) -> None:
    if self.phase.value != "created":
      raise RuntimeError(f"{what} cannot be added after the service starts.")

  # Introspection ---------------------------------------------------------------

  @property
  def client(self) -> Client:
    """A `Client` bound to this service's runtime."""
    if self._client is None:
      raise RuntimeError(f"Service {self.name!r} has not started.")
    return self._client

  def metadata(self) -> dict[str, JsonValue]:
    """What this service advertises in the presence table."""
    requests: dict[str, JsonValue] = {
      request_id: schema.hash
      for request_id, (schema, _) in sorted(self._requests.items())
    }
    events: dict[str, JsonValue] = {
      listener.event.id: listener.event.hash for listener in self._listeners
    }
    work: dict[str, JsonValue] = {
      name: queue.hash for name, (queue, _) in sorted(self._work.items())
    }
    declared: dict[str, JsonValue] = {
      kind: dict(values) for kind, values in sorted(self._declared.items())
    }
    metadata: dict[str, JsonValue] = {
      "version": self.version,
      "requests": requests,
      "events": events,
      "work": work,
      DECLARATIONS_KEY: declared,
    }
    for extension in self._extensions:
      for key, value in extension.metadata().items():
        current = metadata.get(key)
        if isinstance(current, list) and isinstance(value, list):
          merged: list[JsonValue] = [*sorted({*map(str, current), *map(str, value)})]
          metadata[key] = merged
        elif isinstance(current, dict) and isinstance(value, dict):
          metadata[key] = {**current, **value}
        else:
          metadata[key] = value
    return metadata

  # Lifecycle -------------------------------------------------------------------

  async def on_start(self) -> None:
    """Hook: runs once when the component starts."""
    runtime = self.runtime
    self._client = Client(runtime)
    for handler in self._startup:
      await call_handler(self, handler, NO_PAYLOAD)
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
    for handler, interval in self._periodic:
      label = f"{handler.__module__}:{handler.__qualname__}"
      self.spawn(self._run_every(handler, interval, label), name=f"every {label}")
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
    for extension in self._extensions:
      await extension.start(self)
    # Store declaration documents before advertising their hashes.
    for kind, documents in self._declarations.items():
      self._declared[kind] = await Declarations(runtime, kind).store(documents)
    self._presence = await runtime.register(self, metadata=self.metadata())
    self._report_conflicts()

  async def on_drain(self) -> None:
    """Hook: runs when draining begins."""
    await self._stop_sources()

  async def on_close(self) -> None:
    """Hook: runs when the component closes."""
    await self._stop_sources()
    for handler in self._shutdown:
      try:
        await call_handler(self, handler, NO_PAYLOAD)
      except Exception:
        log.exception("A shutdown handler failed", handler=handler.__qualname__)

  async def _stop_sources(self) -> None:
    if self._presence is not None:
      await self.runtime.unregister(self._presence)
      self._presence = None
    subscriptions, self._subscriptions = self._subscriptions, []
    for subscription in subscriptions:
      try:
        await subscription.drain()
      except Exception:
        log.debug("Subscription drain failed", exc_info=True)
    consumers, self._consumers = self._consumers, []
    await asyncio.gather(*(consumer.stop() for consumer in consumers))
    for extension in reversed(self._extensions):
      try:
        await extension.stop()
      except Exception:
        log.exception("Stopping an extension of %s failed", self.name)

  def _report_conflicts(self) -> None:
    mine = set(self._requests)
    for entry in self.runtime.directory.entries("service"):
      if entry.name == self.name:
        continue
      theirs = entry.metadata.get("requests")
      if isinstance(theirs, dict) and (overlap := mine & set(theirs)):
        log.error(
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
      try:
        await self.runtime.respond(message, body, headers=headers)
      except Exception as exc:
        # The answer could not be sent (too large to store, say). Tell the caller
        # why instead of leaving it to time out.
        log.exception("Could not send the reply to %s", schema.id)
        with suppress(Exception):
          await self.runtime.respond(
            message,
            error_body("reply_failed", f"{type(exc).__name__}: {exc}", None),
            headers={STATUS_HEADER: "error"},
          )

  async def _run_request[InputT, OutputT](
    self,
    message: Msg,
    schema: RequestSchema[InputT, OutputT],
    handler: RequestHandler[InputT, OutputT],
  ) -> bytes:
    # Compatibility is decided by validation, not by hash equality, so a
    # rolling update that adds an optional field keeps working both ways.
    expected = (message.headers or {}).get(SCHEMA_HEADER)
    try:
      payload = schema.decode_input_json(await self.runtime.payload(message))
    except ValidationError as exc:
      if expected is not None and expected != schema.hash:
        raise ServiceError(
          "incompatible_schema",
          f"Caller and handler versions of {schema.id!r} are incompatible.",
          detail={"caller": expected, "handler": schema.hash, "errors": _errors(exc)},
        ) from exc
      raise ServiceError(
        "invalid_input",
        f"Input does not match request {schema.id!r}.",
        detail=_errors(exc),
      ) from exc
    call = Call("request", schema.id, self, message, payload)

    async def final(call: Call) -> None:
      call.output = await handler(call.input)

    try:
      with handling(self.name, f"request {schema.id}"):
        await self._call_middleware.run(call, final)
      if call.output is UNSET:
        raise ServiceError(
          "ended_without_reply",
          f"Middleware ended request {schema.id!r} without setting `call.output`.",
        )
      result = call.output
    except ServiceError:
      raise
    except Exception as exc:
      log.exception("Request handler for %s failed", schema.id)
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
    if not self.ordered_by_guild:
      await self._run_listeners(message)
      return
    # In-order per guild within this replica: handlers for one guild never overlap.
    guild = _guild_of(message.subject)
    lock = self._guild_locks.setdefault(guild, asyncio.Lock())
    try:
      async with lock:
        await self._run_listeners(message)
    finally:
      if not lock.locked() and not lock._waiters:  # pyright: ignore[reportPrivateUsage]
        self._guild_locks.pop(guild, None)

  async def _run_listeners(self, message: Msg) -> None:
    matching = [
      listener
      for listener in self._listeners
      if listener.event.matches(message.subject)
    ]
    if not matching:
      # A newer replica updated the shared consumer; let it take this event.
      raise Retry(1.0)
    guild = _guild_of(message.subject)
    sequence = message.metadata.sequence.stream if message.metadata.sequence else 0
    done = self._succeeded.get(sequence, set())
    decoded: dict[str, Any] = {}
    runs: list[tuple[int, _Listener, Awaitable[None]]] = []
    for index, listener in enumerate(self._listeners):
      if listener not in matching or index in done:
        continue
      if listener.guild_id is not None and guild != listener.guild_id:
        continue
      event = listener.event
      if event.id not in decoded:
        try:
          decoded[event.id] = event.decode_json(message.data)
        except ValidationError as exc:
          self._undecodable("events", event.id, event.hash, exc)
      runs.append((index, listener, self._listen(listener, message, decoded[event.id])))
    results = await asyncio.gather(*(run for *_, run in runs), return_exceptions=True)
    failures: list[tuple[_Listener, BaseException]] = []
    for (index, listener, _), result in zip(runs, results):
      if isinstance(result, BaseException):
        failures.append((listener, result))
      else:
        done.add(index)
    for listener, error in failures:
      log.error(
        "Handler %s failed for event %s",
        listener.label,
        listener.event.id,
        exc_info=error,
      )
    if failures:
      # Remember who succeeded so a redelivery to this replica re-runs only failures.
      self._succeeded[sequence] = done
      raise Retry(min(2.0 ** ((message.metadata.num_delivered or 1) - 1), 60.0))
    self._succeeded.pop(sequence, None)

  async def _listen(self, listener: _Listener, message: Msg, payload: Any) -> None:
    """Run one listener; a failing `when` predicate fails only that listener."""
    if listener.when is not None and not listener.when(payload):
      return
    await self._through("event", listener.event.id, message, payload, listener.handler)

  async def _through(
    self,
    kind: Literal["event", "work"],
    key: str,
    message: Msg,
    payload: Any,
    handler: EventHandler[Any],
  ) -> None:
    """Run a handler inside the middleware stack. `end()` counts as handled."""

    async def final(call: Call) -> None:
      await call_handler(self, handler, call.input, call.message)

    with handling(self.name, f"{kind} {key}"):
      await self._call_middleware.run(Call(kind, key, self, message, payload), final)

  def _undecodable(
    self, kind: str, key: str, mine: str, error: ValidationError
  ) -> Never:
    """Retry while replicas run other schema versions; reject once they agree."""
    versions: set[str] = set()
    for entry in self.runtime.directory.entries(self.kind):
      declared = entry.metadata.get(kind)
      if entry.name == self.name and isinstance(declared, dict):
        versions.add(str(declared.get(key)))
    if versions - {mine}:
      log.warning(
        "%s %s does not match this replica's schema; leaving it for another version",
        kind,
        key,
      )
      raise Retry(1.0) from error
    log.error("%s %s does not match its schema: %s", kind, key, error)
    raise Reject from error

  def _work_callback[T](
    self, queue: WorkQueue[T], handler: EventHandler[T]
  ) -> Callable[[Msg], Awaitable[None]]:
    async def callback(message: Msg) -> None:
      try:
        job = queue.decode_json(message.data)
      except ValidationError as exc:
        self._undecodable("work", queue.name, queue.hash, exc)
      await self._through("work", queue.name, message, job, handler)

    return callback


def _guild_of(subject: str) -> int | None:
  last = subject.rsplit(".", 1)[-1]
  return int(last) if last.isdecimal() else None


def _errors(exc: ValidationError) -> JsonValue:
  return [
    {"path": [str(part) for part in error["loc"]], "message": error["msg"]}
    for error in exc.errors(include_url=False)
  ]


def _require_async(handler: object, what: str) -> None:
  if not inspect.iscoroutinefunction(handler):
    raise TypeError(f"{what} must be async functions.")
