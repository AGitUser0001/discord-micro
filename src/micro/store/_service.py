import asyncio
import logging
from collections.abc import Sequence
from typing import Any

from pydantic import JsonValue

from micro.runtime import Runtime
from micro.service import Client, RequestSchema, Service

from ._module import GraphModule
from ._store import GraphEngine, GraphExecutor, GraphQLBody
from .composer import DirectiveMetadata, TypeDirectiveMetadata

logger = logging.getLogger("micro")

STORE_EXECUTE = RequestSchema[GraphQLBody, dict[str, JsonValue]](
  id="micro.store.execute",
  input=GraphQLBody,
  output=dict[str, JsonValue],
)


class Store(Service):
  """An optional graph store, run as an ordinary service.

  It serves the union of the graph modules that live services declare with
  `Service.uses`, plus any passed here, and recomposes as services come and go.
  No builtin requires it.
  """

  def __init__(
    self,
    executor: GraphExecutor,
    *,
    modules: Sequence[GraphModule] = (),
    directives: Sequence[DirectiveMetadata] = (),
    type_directives: Sequence[TypeDirectiveMetadata] = (),
    name: str = "store",
  ) -> None:
    super().__init__(name)
    self.engine = GraphEngine(
      executor, directives=directives, type_directives=type_directives
    )
    self._static = {module.id: module for module in modules}
    self._compose_requested = asyncio.Event()
    self.handle(STORE_EXECUTE)(self._execute)

  @property
  def ready(self) -> bool:
    return super().ready and self.engine.available

  async def on_start(self) -> None:
    await self.engine.executor.start()
    await super().on_start()
    self._unwatch = self.runtime.directory.on_change(self._compose_requested.set)
    await self._compose()
    self.spawn(self._compose_loop(), name="compose")

  async def on_close(self) -> None:
    self._unwatch()
    await super().on_close()
    await self.engine.executor.close()

  def declared_modules(self) -> tuple[GraphModule, ...]:
    """The module set live services currently declare."""
    modules: dict[str, GraphModule] = dict(self._static)
    for entry in self.runtime.directory.entries("service"):
      declared = entry.metadata.get("modules")
      if not isinstance(declared, list):
        continue
      for item in declared:
        module = GraphModule.model_validate(item)
        existing = modules.get(module.id)
        if existing is not None and existing.graphql_schema != module.graphql_schema:
          raise ValueError(
            f"Services declare different schemas for graph module {module.id!r}."
          )
        modules[module.id] = module
    return tuple(modules.values())

  async def _compose(self) -> None:
    try:
      await self.engine.apply_modules(self.declared_modules())
    except Exception:
      logger.exception("Store could not compose the declared graph modules")

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
    return await self._client.request(
      STORE_EXECUTE,
      GraphQLBody.model_validate(
        {"query": query, "variables": variables, "operationName": operation_name}
      ),
    )
