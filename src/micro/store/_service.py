import asyncio
import json
import os
from collections.abc import AsyncGenerator, Callable, Sequence
from contextlib import suppress
from contextvars import ContextVar
from dataclasses import dataclass
from string.templatelib import Interpolation, Template
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from nats.aio.msg import Msg
from pydantic import BaseModel, JsonValue

from micro import log, subjects
from micro.coordination import Declarations
from micro.errors import MicroError
from micro.result import Err, Ok, Result
from micro.runtime import Runtime, default_backoff
from micro.service import Client, RequestSchema, Service

from ._module import GraphModule
from ._store import GraphEngine, GraphExecutor, GraphQLBody

if TYPE_CHECKING:
  from micro.discord import Context
from .composer import DirectiveMetadata, GraphCompositionError, TypeDirectiveMetadata

DEFAULT_STORE_URL = "sqlite:.micro/store.db"


def executor_from_url(url: str) -> GraphExecutor:
  """`sqlite:PATH` (the embedded default); bring other databases as executors."""
  if url.startswith("sqlite:"):
    from .sqlite import SQLiteGraph

    return SQLiteGraph(
      url.removeprefix("sqlite:").removeprefix("//") or ".micro/store.db"
    )
  raise ValueError(
    f"Unsupported MICRO_STORE_URL {url!r}; pass Store(executor=...) for other databases."
  )


STORE_EXECUTE = RequestSchema[GraphQLBody, dict[str, JsonValue]](
  id="micro.store.execute",
  input=GraphQLBody,
  output=dict[str, JsonValue],
)


class TransactionStart(BaseModel):
  """`micro.store.begin`: open a transaction for the client registered under `id`."""

  id: str


class TransactionStarted(BaseModel):
  """Where the transaction's operations go: the subject of the replica holding it."""

  subject: str


STORE_BEGIN = RequestSchema[TransactionStart, TransactionStarted](
  id="micro.store.begin",
  input=TransactionStart,
  output=TransactionStarted,
)

TRANSACTION_KIND = "store-transaction"
"""The presence kind a client holds while its transaction is open: when it is gone (the
client ended it, or its process died and the entry expired), the Store rolls back."""


class _Ended(Exception):
  """Leaves a transaction's block so it rolls back; `reply` gets told it did."""

  def __init__(self, reply: Msg | None = None) -> None:
    self.reply = reply


class Store(Service):
  """An optional graph store, run as an ordinary service.

  It serves the graph modules services declare with `Service.uses` (plus any
  passed here). Modules converge: a new version is composed only when every
  live declarer agrees on it, modules of stopped services are retained, and a
  module set that fails to compose leaves the last good graph serving. No
  builtin requires it.
  """

  def __init__(
    self,
    executor: GraphExecutor | None = None,
    *,
    modules: Sequence[GraphModule] = (),
    directives: Sequence[DirectiveMetadata] = (),
    type_directives: Sequence[TypeDirectiveMetadata] = (),
    name: str = "store",
  ) -> None:
    super().__init__(name)
    self.engine = GraphEngine(
      executor
      or executor_from_url(os.environ.get("MICRO_STORE_URL", DEFAULT_STORE_URL)),
      directives=directives,
      type_directives=type_directives,
    )
    self._static = {module.id: module for module in modules}
    self._compose_requested = asyncio.Event()
    self._pending: dict[str, str] = {}
    self.handle(STORE_EXECUTE)(self._execute)
    self.handle(STORE_BEGIN)(self._begin)

  @property
  def ready(self) -> bool:
    """Whether a schema has composed and the store can serve."""
    return super().ready and self.engine.available

  async def on_start(self) -> None:
    """Open the executor and begin composing declared graph modules."""
    await self.engine.executor.start()
    await super().on_start()
    self._unwatch = self.runtime.directory.on_change(
      self._compose_requested.set,
      watching=Declarations(self.runtime, "modules").live,
    )
    await self._compose()
    self.spawn(self._compose_loop(), name="compose")

  async def on_close(self) -> None:
    """Close the executor."""
    self._unwatch()
    await super().on_close()
    await self.engine.executor.close()

  async def declared_modules(self) -> tuple[GraphModule, ...]:
    """The converged module set: each module at the version every live declarer
    agrees on, the applied version during a rollout, and retained modules whose
    services are not running right now."""
    view = await Declarations(self.runtime, "modules").view()
    modules: dict[str, GraphModule] = dict(self._static)
    for key, declared in view.items():
      modules[key] = GraphModule.model_validate(declared.document)
    self._pending = {key: declared.hash for key, declared in view.items()}
    return tuple(modules.values())

  async def _compose(self) -> None:
    try:
      modules = await self.declared_modules()
      await self.engine.apply_modules(modules)
    except GraphCompositionError as error:  # a schema mistake: the message says it all
      log.error("Store keeps its last good graph; the new module set failed: %s", error)
      return
    except Exception:
      log.exception("Store keeps its last good graph; the new module set failed")
      return
    declarations = Declarations(self.runtime, "modules")
    for key, value in self._pending.items():
      await declarations.mark_applied(key, value)

  async def _compose_loop(self) -> None:
    failures = 0
    while True:
      await self._compose_requested.wait()
      self._compose_requested.clear()
      try:
        await self._compose()
        failures = 0
      except asyncio.CancelledError:
        raise
      except Exception:
        # Recording what was applied failed (NATS trouble): try the pass again.
        failures += 1
        log.warning("The store could not record its modules", exc_info=True)
        await asyncio.sleep(default_backoff(failures))
        self._compose_requested.set()

  async def _execute(self, ctx: Context, body: GraphQLBody) -> dict[str, JsonValue]:
    return await self.engine.execute(body)

  # Transactions over several requests -------------------------------------------

  async def _begin(self, ctx: Context, start: TransactionStart) -> TransactionStarted:
    subject = f"{subjects.PREFIX}.store.transaction.{subjects.token(start.id)}"
    opened: asyncio.Future[None] = asyncio.get_running_loop().create_future()
    self.spawn(
      self._transaction(start.id, subject, opened), name=f"transaction.{start.id}"
    )
    await opened  # the transaction holds the store now; a failure to open raises here
    return TransactionStarted(subject=subject)

  async def _transaction(
    self, client: str, subject: str, opened: asyncio.Future[None]
  ) -> None:
    """Hold one executor transaction, running the operations sent to `subject`, until the
    client commits, rolls back, an operation fails, or the client is gone."""
    runtime = self.runtime
    operations: asyncio.Queue[Msg] = asyncio.Queue()
    gone = asyncio.Event()
    seen = False

    def check() -> None:
      nonlocal seen
      present = any(
        entry.id == client for entry in runtime.directory.entries(TRANSACTION_KIND)
      )
      seen = seen or present
      if seen and not present:
        gone.set()

    async def reply(message: Msg, value: object) -> None:
      await runtime.respond(message, json.dumps(value).encode())

    unwatch = runtime.directory.on_change(check)
    check()
    subscription = await runtime.nats.subscribe(subject, cb=operations.put)
    commit: Msg | None = None
    try:
      async with self.engine.executor.transaction(writes=True) as transaction:
        opened.set_result(None)
        while commit is None:
          received = asyncio.ensure_future(operations.get())
          ended = asyncio.ensure_future(gone.wait())
          await asyncio.wait({received, ended}, return_when=asyncio.FIRST_COMPLETED)
          ended.cancel()
          if not received.done():
            received.cancel()
            raise _Ended  # the client is gone: nothing it did is kept
          message = received.result()
          request = json.loads(await runtime.payload(message))
          if request["op"] == "commit":
            commit = message
          elif request["op"] == "rollback":
            raise _Ended(message)
          else:
            response = await self.engine.execute(
              GraphQLBody.model_validate(request["body"]), transaction=transaction
            )
            await reply(message, response)
            if response.get("errors"):
              raise _Ended  # a failed operation ends the transaction: all of it undone
      await reply(commit, {})
    except _Ended as ended:
      if ended.reply is not None:
        await reply(ended.reply, {})
    except Exception as error:
      if not opened.done():
        opened.set_exception(error)
      elif commit is not None:  # the commit itself failed: nothing was kept
        message = str(error) or type(error).__name__
        extensions = getattr(error, "extensions", None) or {
          "code": "UNAVAILABLE",
          "retryable": True,
        }
        await reply(
          commit, {"errors": [{"message": message, "extensions": extensions}]}
        )
      else:
        raise
    finally:
      if not opened.done():
        opened.set_exception(
          RuntimeError("The store closed before the transaction opened.")
        )
      await subscription.unsubscribe()
      unwatch()


@dataclass(eq=False)
class StoreError(MicroError):
  """The store refused an operation. Raised as the subclass for its kind, so
  `except Conflict:` and `result.ignore(Conflict)` work: `Conflict`, `Unavailable`,
  `Invalid` or `BadQuery`. It is the first of the store's errors; all are in `errors`."""

  message: str
  code: str | None = None
  """The store's error code exactly as it sent it (`"CONFLICT"`, ...), even one this version
  does not know; None for a mistake in the query (`BadQuery`)."""
  retryable: bool = False
  """Whether trying the same operation again may succeed."""
  path: tuple[str | int, ...] = ()
  """Which field of the operation failed, if one did."""
  errors: tuple[dict[str, Any], ...] = ()
  """Every error the store returned, as GraphQL formats them."""

  def __str__(self) -> str:
    return f"{self.code}: {self.message}" if self.code else self.message


class Conflict(StoreError):
  """A write the store refused because the key exists (an insert or connect of something
  already there): update it instead, or `result.ignore(Conflict)` to mean "already there"."""


class Unavailable(StoreError):
  """The store is busy or still starting; the same operation may work if tried again."""


class Invalid(StoreError):
  """The store's backend refused the operation's statement."""


class BadQuery(StoreError):
  """A mistake in the query itself: a syntax error, an unknown field, a missing argument,
  a value of the wrong type. Trying again will not help; the query must change."""


_KINDS: dict[str | None, type[StoreError]] = {
  "CONFLICT": Conflict,
  "UNAVAILABLE": Unavailable,
  "INVALID": Invalid,
  None: BadQuery,
}


def store_error(errors: list[dict[str, Any]]) -> StoreError:
  """The `StoreError` for the store's GraphQL `errors`: the subclass for the first one's
  code, or the base class for a code this version does not know (the code is kept)."""
  first = errors[0]
  extensions = first.get("extensions") or {}
  raw = extensions.get("code")
  code = None if raw is None else str(raw)
  kind = _KINDS.get(code, StoreError)
  return kind(
    message=str(first.get("message", "")),
    code=code,
    retryable=bool(extensions.get("retryable")) or kind is Unavailable,
    path=tuple(first.get("path") or ()),
    errors=tuple(errors),
  )


type Steps[T, E: Exception] = AsyncGenerator[Template | Ok[T] | Err[E], dict[str, Any]]
"""A transaction's steps (see `StoreClient.transaction`): it yields each query as a
t-string and gets its `data` back, then yields `Ok(value)` to commit or `Err(error)` to
roll back."""

_IN_TRANSACTION: ContextVar[bool] = ContextVar("micro_store_transaction", default=False)


def _body(query: Template, operation_name: str | None = None) -> GraphQLBody:
  """A t-string as GraphQL text, each value sent separately as a variable ($v0, ...)."""
  if not isinstance(query, Template):
    raise TypeError('execute takes a t-string: t"{ ... }"')
  text: list[str] = []
  variables: dict[str, Any] = {}
  for part in query:
    if isinstance(part, Interpolation):
      name = f"v{len(variables)}"
      variables[name] = part.value
      text.append(f"${name}")
    else:
      text.append(part)
  return GraphQLBody.model_validate(
    {"query": "".join(text), "variables": variables, "operationName": operation_name}
  )


class StoreClient:
  """Executes GraphQL against whichever store replica answers."""

  def __init__(self, runtime: Runtime | Client) -> None:
    self._client = runtime if isinstance(runtime, Client) else Client(runtime)

  async def execute(
    self, query: Template, *, operation_name: str | None = None
  ) -> Result[dict[str, Any], StoreError]:
    """Run a GraphQL query or mutation, written as a t-string.

    Each `{value}` is sent as a GraphQL variable, never pasted into the text, so any
    value is safe, quotes and all. Write it bare where the value goes; the store types
    it from the argument it is passed to. Braces of the query itself are doubled:

      await store.execute(t"mutation {{ addUser(id: {user_id}) {{ id }} }}")

    Returns:
      `Ok(data)`, the operation's `data`; or `Err(StoreError)` when the store refused it
      (a mistake in the query, `CONFLICT`, `UNAVAILABLE`). The store never answers with
      part of the data: an operation succeeds or fails whole.

    Raises:
      RoutingError, RequestTimeoutError: The store could not be reached. That is broken
        infrastructure, not an answer, so it raises.
    """
    if _IN_TRANSACTION.get():
      raise RuntimeError(
        "A store transaction is running here: yield the query from its steps instead "
        "(this call would wait for the transaction to end, and it is waiting for you)."
      )
    response: dict[str, Any] = await self._client.request(
      STORE_EXECUTE, _body(query, operation_name)
    )
    errors = response.get("errors")
    if errors:
      return Err(store_error(errors))
    return Ok(response.get("data") or {})

  async def transaction[**P, T, E: Exception](
    self, steps: Callable[P, Steps[T, E]], /, *args: P.args, **kwargs: P.kwargs
  ) -> Result[T, E | StoreError]:
    """Run `steps(*args, **kwargs)` as one transaction: queries, your code between them,
    and either all of it is kept or none of it::

      async def buy(gid: str, price: int) -> Steps[int, NotEnough]:
        data = yield t"{{ guild(id: {gid}) {{ coins }} }}"
        coins = data["guild"]["coins"]
        if coins < price:
          yield Err(NotEnough(coins))  # rolls back
        yield t"mutation {{ setCoins(id: {gid}, coins: {coins - price}) {{ id }} }}"
        yield Ok(coins - price)  # commits

      match await store.transaction(buy, gid, price): ...

    Returns:
      What the steps yielded last: `Ok(value)` once committed, or their `Err(error)`
      (rolled back); or `Err(StoreError)` if the store refused a query (rolled back, and
      the steps stop there) or the commit.

    The transaction holds the store while it runs (with SQLite, every other write waits),
    so keep slow work (Discord calls, downloads) outside it. If this process dies, the
    store rolls back when its presence expires. An exception in the steps rolls back and
    propagates.
    """
    if _IN_TRANSACTION.get():
      raise RuntimeError("Store transactions do not nest: yield the queries instead.")
    runtime = self._client.runtime
    client = uuid4().hex
    presence = await runtime.register(kind=TRANSACTION_KIND, name="store", id=client)
    entered = _IN_TRANSACTION.set(True)
    try:
      started = await self._client.request(STORE_BEGIN, TransactionStart(id=client))

      async def send(message: str) -> dict[str, Any]:
        reply = await runtime.request(
          started.subject, message.encode(), timeout=self._client.timeout
        )
        return json.loads(reply.data)

      generator = steps(*args, **kwargs)
      try:
        step = await generator.asend(None)  # pyright: ignore[reportArgumentType]
        while isinstance(step, Template):
          body = _body(step).model_dump_json(by_alias=True)
          response = await send(f'{{"op": "execute", "body": {body}}}')
          if response.get("errors"):  # the store has rolled back already
            return Err(store_error(response["errors"]))
          step = await generator.asend(response.get("data") or {})
        if not isinstance(step, Ok | Err):
          raise TypeError(
            "A transaction's steps yield t-strings, then Ok(value) or Err(error); "
            f"not {type(step).__name__}."
          )
      except StopAsyncIteration:
        with suppress(Exception):
          await send('{"op": "rollback"}')
        raise TypeError(
          "A transaction's steps must end with `yield Ok(value)` (commit) or "
          "`yield Err(error)` (roll back)."
        ) from None
      except BaseException:
        with suppress(Exception):
          await send('{"op": "rollback"}')
        raise
      finally:
        await generator.aclose()
      if isinstance(step, Err):
        await send('{"op": "rollback"}')
        return step
      committed = await send('{"op": "commit"}')
      if committed.get("errors"):
        return Err(store_error(committed["errors"]))
      return step
    finally:
      _IN_TRANSACTION.reset(entered)
      await runtime.unregister(presence)
