import asyncio
import logging
import os
from collections.abc import Sequence
from typing import Any

from pydantic import JsonValue

from micro.coordination import Declarations
from micro.runtime import Runtime
from micro.service import Client, RequestSchema, Service

from ._module import GraphModule
from ._store import GraphEngine, GraphExecutor, GraphQLBody
from .composer import DirectiveMetadata, TypeDirectiveMetadata

logger = logging.getLogger("micro")

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
      logger.exception("Store keeps its last good graph; the new module set failed")
      return
    declarations = Declarations(self.runtime, "modules")
    for key, value in self._pending.items():
      await declarations.mark_applied(key, value)

  async def _compose_loop(self) -> None:
    while True:
      await self._compose_requested.wait()
      self._compose_requested.clear()
      await self._compose()

  async def _execute(self, body: GraphQLBody) -> dict[str, JsonValue]:
    return await self.engine.execute(body)


class StoreClient:
  """Executes GraphQL against whichever store replica answers."""

  def __init__(self, runtime: Runtime | Client) -> None:
    self._client = runtime if isinstance(runtime, Client) else Client(runtime)

  async def execute(
    self,
    query: str,
    *,
    variables: dict[str, Any] | None = None,
    operation_name: str | None = None,
  ) -> dict[str, Any]:
    """Run a GraphQL query or mutation; returns `{"data", "errors"}` and raises only if the store cannot be reached."""
    return await self._client.request(
      STORE_EXECUTE,
      GraphQLBody.model_validate(
        {"query": query, "variables": variables, "operationName": operation_name}
      ),
    )
