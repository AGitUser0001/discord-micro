from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from json import JSONDecodeError
from types import MappingProxyType
from typing import Any, Protocol

from graphglot.dialect import Dialect
from graphql import (
  DocumentNode,
  FieldNode,
  GraphQLError,
  GraphQLSchema,
  OperationDefinitionNode,
  build_schema,
  execute_sync,
  extend_schema,
  get_operation_ast,
  parse,
  print_schema,
  validate,
)
from graphql.error import GraphQLSyntaxError
from graphql.execution.values import get_variable_values
from pydantic import BaseModel, ConfigDict, Field
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse, Response
from starlette.routing import Route
from starlette.types import Receive, Scope, Send

from micro._store_module import StoreModule
from micro.service import JsonValue

type ResultShaper = Callable[[GraphResult], Mapping[str, JsonValue]]


class StoreTopology(BaseModel):
  """The overseer-controlled module set exposed by a store instance."""

  model_config = ConfigDict(extra="forbid", frozen=True)

  revision: int = Field(ge=0)
  modules: tuple[StoreModule, ...]


@dataclass(frozen=True, slots=True)
class GraphStatement:
  """A canonical ISO GQL statement and its bound parameters."""

  text: str
  parameters: Mapping[str, JsonValue] = field(default_factory=dict)
  columns: tuple[str, ...] = ()

  def __post_init__(self) -> None:
    if not self.text.strip():
      raise ValueError("A graph statement cannot be empty.")
    validation = Dialect.get_or_raise("fullgql").validate(self.text)
    if not validation.success:
      diagnostics = "; ".join(str(item) for item in validation.diagnostics)
      raise ValueError(f"Graph statement is not valid ISO GQL: {diagnostics}")
    if len(set(self.columns)) != len(self.columns) or any(
      not column.isidentifier() for column in self.columns
    ):
      raise ValueError("Graph result columns must be unique identifiers.")
    object.__setattr__(self, "parameters", MappingProxyType(dict(self.parameters)))


@dataclass(frozen=True, slots=True)
class GraphResult:
  rows: tuple[Mapping[str, JsonValue], ...]


@dataclass(frozen=True, slots=True)
class GraphQLRequest:
  schema: GraphQLSchema
  document: DocumentNode
  operation: OperationDefinitionNode
  variables: Mapping[str, Any]
  operation_name: str | None


@dataclass(frozen=True, slots=True)
class CompiledOperation:
  statement: GraphStatement
  shape: ResultShaper


class GraphCompiler(Protocol):
  def compile(self, request: GraphQLRequest) -> CompiledOperation: ...


class _UnavailableCompiler:
  def compile(self, request: GraphQLRequest) -> CompiledOperation:
    raise GraphQLError("The selected field has no active GraphQL module.")


class GraphExecutor(Protocol):
  async def start(self) -> None: ...

  async def execute(self, statement: GraphStatement) -> GraphResult: ...

  async def close(self) -> None: ...


class ModuleComposer(Protocol):
  """Builds one compiler for an overseer-provided set of store modules."""

  def compose(
    self,
    base: GraphCompiler,
    modules: Sequence[StoreModule],
  ) -> GraphCompiler: ...


@dataclass(frozen=True, slots=True)
class _StoreRuntime:
  schema: GraphQLSchema
  compiler: GraphCompiler
  module_ids: tuple[str, ...]


class Store:
  """Database-neutral GraphQL ASGI frontend for a graph store."""

  def __init__(
    self,
    schema: GraphQLSchema | str | None = None,
    *,
    compiler: GraphCompiler | None = None,
    executor: GraphExecutor,
    module_composer: ModuleComposer | None = None,
  ) -> None:
    schema = schema or "type Query { _micro: Boolean }"
    self._base_schema = build_schema(schema) if isinstance(schema, str) else schema
    self._base_compiler = compiler or _UnavailableCompiler()
    self.executor = executor
    self._module_composer = module_composer
    self._runtime = _StoreRuntime(self._base_schema, self._base_compiler, ())
    self._topology_revision = -1
    self._ready = False
    self._app = Starlette(
      routes=[
        Route("/graphql", self._graphql, methods=["POST"]),
        Route("/schema", self._schema, methods=["GET"]),
        Route("/topology", self._topology, methods=["POST"]),
        Route("/health/live", self._live, methods=["GET"]),
        Route("/health/ready", self._health_ready, methods=["GET"]),
      ]
    )

  async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
    if scope["type"] != "lifespan":
      await self._app(scope, receive, send)
      return
    await self._lifespan(receive, send)

  async def _graphql(self, request: Request) -> Response:
    if not self._ready:
      return self._errors("Store is not ready.", status_code=503)
    content_type = request.headers.get("content-type", "").partition(";")[0].strip()
    if content_type != "application/json":
      return self._errors("GraphQL requests require application/json.", status_code=415)

    try:
      body: Any = await request.json()
    except JSONDecodeError, UnicodeDecodeError:
      return self._errors("Request body is not valid JSON.", status_code=400)
    if not isinstance(body, dict):
      return self._errors("GraphQL request body must be an object.", status_code=400)

    query = body.get("query")
    variables = body.get("variables")
    operation_name = body.get("operationName")
    if not isinstance(query, str):
      return self._errors("GraphQL request requires a string query.", status_code=400)
    if variables is not None and not isinstance(variables, dict):
      return self._errors(
        "GraphQL variables must be an object or null.", status_code=400
      )
    if operation_name is not None and not isinstance(operation_name, str):
      return self._errors(
        "GraphQL operationName must be a string or null.", status_code=400
      )

    runtime = self._runtime
    try:
      document = parse(query)
    except GraphQLSyntaxError as exc:
      return JSONResponse({"errors": [exc.formatted]}, status_code=400)
    if errors := validate(runtime.schema, document):
      return JSONResponse(
        {"errors": [error.formatted for error in errors]}, status_code=400
      )
    operation = get_operation_ast(document, operation_name)
    if operation is None:
      return self._errors("GraphQL operation could not be selected.", status_code=400)

    coerced = get_variable_values(
      runtime.schema,
      operation.variable_definitions or (),
      variables or {},
    )
    if isinstance(coerced, list):
      return JSONResponse(
        {"errors": [error.formatted for error in coerced]}, status_code=400
      )

    if self._is_introspection(operation):
      result = execute_sync(
        runtime.schema,
        document,
        variable_values=coerced,
        operation_name=operation_name,
      )
      response: dict[str, Any] = {"data": result.data}
      if result.errors:
        response["errors"] = [error.formatted for error in result.errors]
      return JSONResponse(response)

    graphql_request = GraphQLRequest(
      runtime.schema,
      document,
      operation,
      MappingProxyType(coerced),
      operation_name,
    )
    try:
      compiled = runtime.compiler.compile(graphql_request)
      result = await self.executor.execute(compiled.statement)
      data = dict(compiled.shape(result))
    except GraphQLError as exc:
      return JSONResponse({"data": None, "errors": [exc.formatted]})
    return JSONResponse({"data": data})

  async def _schema(self, request: Request) -> Response:
    return PlainTextResponse(
      print_schema(self._runtime.schema), media_type="text/plain"
    )

  async def _topology(self, request: Request) -> Response:
    if (
      request.headers.get("content-type", "").partition(";")[0].strip()
      != "application/json"
    ):
      return self._errors("Store topology requires application/json.", status_code=415)
    try:
      topology = StoreTopology.model_validate_json(await request.body())
      self.apply_topology(topology)
    except (TypeError, ValueError) as exc:
      return JSONResponse(
        {"errors": [{"message": "Store topology was rejected.", "detail": str(exc)}]},
        status_code=409,
      )
    return Response(status_code=204)

  def apply_topology(self, topology: StoreTopology) -> None:
    if topology.revision < self._topology_revision:
      raise ValueError(
        f"Topology revision {topology.revision} is older than {self._topology_revision}."
      )
    if topology.revision == self._topology_revision:
      return
    module_ids = tuple(module.id for module in topology.modules)
    if len(set(module_ids)) != len(module_ids):
      raise ValueError("Store topology contains duplicate module IDs.")
    if topology.modules and self._module_composer is None:
      from micro._federation import compose_federation

      from ._compiler import FederationCompiler

      graph = compose_federation(topology.modules)
      schema = graph.schema
      compiler: GraphCompiler = FederationCompiler(graph)
    elif topology.modules:
      schema = self._base_schema
      for module in topology.modules:
        schema = extend_schema(schema, parse(module.graphql_schema))
      assert self._module_composer is not None
      compiler = self._module_composer.compose(self._base_compiler, topology.modules)
    else:
      schema = self._base_schema
      compiler = self._base_compiler
    self._runtime = _StoreRuntime(schema, compiler, module_ids)
    self._topology_revision = topology.revision

  @property
  def active_modules(self) -> tuple[str, ...]:
    return self._runtime.module_ids

  @property
  def topology_revision(self) -> int:
    return self._topology_revision

  async def _live(self, request: Request) -> Response:
    return Response(status_code=204)

  async def _health_ready(self, request: Request) -> Response:
    return Response(status_code=204 if self._ready else 503)

  async def _lifespan(self, receive: Receive, send: Send) -> None:
    while True:
      message = await receive()
      if message["type"] == "lifespan.startup":
        try:
          await self.executor.start()
        except BaseException as exc:
          await send({"type": "lifespan.startup.failed", "message": str(exc)})
          return
        self._ready = True
        await send({"type": "lifespan.startup.complete"})
      elif message["type"] == "lifespan.shutdown":
        self._ready = False
        try:
          await self.executor.close()
        except BaseException as exc:
          await send({"type": "lifespan.shutdown.failed", "message": str(exc)})
          return
        await send({"type": "lifespan.shutdown.complete"})
        return

  @staticmethod
  def _is_introspection(operation: OperationDefinitionNode) -> bool:
    return bool(operation.selection_set.selections) and all(
      isinstance(selection, FieldNode) and selection.name.value.startswith("__")
      for selection in operation.selection_set.selections
    )

  @staticmethod
  def _errors(message: str, *, status_code: int) -> JSONResponse:
    return JSONResponse({"errors": [{"message": message}]}, status_code=status_code)
