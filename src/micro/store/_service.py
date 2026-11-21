import asyncio
import os
from collections.abc import Sequence
from dataclasses import dataclass
from string.templatelib import Interpolation, Template
from typing import TYPE_CHECKING, Any

from pydantic import JsonValue

from micro import log
from micro.coordination import Declarations
from micro.errors import MicroError
from micro.result import Err, Ok, Result
from micro.runtime import Runtime, default_backoff
from micro.service import Client, RequestSchema, Service

from ._module import GraphModule
from ._store import GraphEngine, GraphExecutor, GraphQLBody

if TYPE_CHECKING:
  from micro.discord import Context
from .composer import DirectiveMetadata, TypeDirectiveMetadata

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
    response: dict[str, Any] = await self._client.request(
      STORE_EXECUTE,
      GraphQLBody.model_validate(
        {
          "query": "".join(text),
          "variables": variables,
          "operationName": operation_name,
        }
      ),
    )
    errors = response.get("errors")
    if errors:
      return Err(store_error(errors))
    return Ok(response.get("data") or {})
