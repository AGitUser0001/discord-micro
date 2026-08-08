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
  get_operation_ast,
  parse,
  print_schema,
  validate,
)
from graphql.error import GraphQLSyntaxError
from graphql.execution.values import get_variable_values
from pydantic import BaseModel, ConfigDict, Field, JsonValue
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse, Response

from micro._microservices import Microservice

from ._module import GraphModule
from .composer import DirectiveMetadata, TypeDirectiveMetadata

type ResultShaper = Callable[[GraphResult], Mapping[str, JsonValue]]


class StoreTopology(BaseModel):
  """The overseer-controlled module set exposed by a store instance."""

  model_config = ConfigDict(extra="forbid", frozen=True)

  revision: int = Field(ge=0)
  modules: tuple[GraphModule, ...]


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


class _Compiler(Protocol):
  def compile(self, request: GraphQLRequest) -> CompiledOperation: ...


class _UnavailableCompiler:
  def compile(self, request: GraphQLRequest) -> CompiledOperation:
    raise GraphQLError("The selected field has no active GraphQL module.")


class GraphExecutor(Protocol):
  async def start(self) -> None: ...

  async def execute(self, statement: GraphStatement) -> GraphResult: ...

  async def close(self) -> None: ...


@dataclass(frozen=True, slots=True)
class _StoreRuntime:
  schema: GraphQLSchema
  compiler: _Compiler
  module_ids: tuple[str, ...]


class Store(Microservice):
  """Database-neutral GraphQL ASGI frontend for a graph store."""

  def __init__(
    self,
    *,
    executor: GraphExecutor,
    directives: Sequence[DirectiveMetadata] = (),
    type_directives: Sequence[TypeDirectiveMetadata] = (),
  ) -> None:
    super().__init__("store")
    empty_schema = build_schema("type Query { _micro: Boolean }")
    self.executor = executor
    self._directives = tuple(directives)
    self._type_directives = tuple(type_directives)
    self._runtime = _StoreRuntime(empty_schema, _UnavailableCompiler(), ())
    self._topology_revision = -1
    self._desired_topology_revision = -1
    self._composition_error: str | None = None
    self._graph_available = True
    self.add_route("/graphql", self._graphql, methods=("POST",), name="store:graphql")
    self.add_route(
      "/topology", self._topology, methods=("POST",), name="store:topology"
    )

  @property
  def component_ready(self) -> bool:
    return self._graph_available

  async def start(self) -> None:
    await self.executor.start()

  async def close(self) -> None:
    await self.executor.close()

  def unavailable_response(self) -> Response:
    return self._unavailable()

  async def _graphql(self, request: Request) -> Response:
    if not self.ready:
      return self._unavailable()
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

  async def _schema_endpoint(self, request: Request) -> Response:
    if not self.ready:
      return self._unavailable()
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
    except (GraphQLError, TypeError, ValueError) as exc:
      return JSONResponse(
        {"errors": [{"message": "Store topology was rejected.", "detail": str(exc)}]},
        status_code=409,
      )
    return Response(status_code=204)

  def apply_topology(self, topology: StoreTopology) -> None:
    if topology.revision < self._desired_topology_revision:
      raise ValueError(
        f"Topology revision {topology.revision} is older than "
        f"{self._desired_topology_revision}."
      )
    if (
      topology.revision == self._topology_revision
      and topology.revision == self._desired_topology_revision
      and self._graph_available
    ):
      return
    self._desired_topology_revision = topology.revision
    self._graph_available = False
    self._composition_error = None
    module_ids = tuple(module.id for module in topology.modules)
    try:
      if len(set(module_ids)) != len(module_ids):
        raise ValueError("Store topology contains duplicate module IDs.")
      if topology.modules:
        from ._compiler import GraphCompiler
        from .composer import compose_graph

        graph = compose_graph(
          topology.modules,
          directives=self._directives,
          type_directives=self._type_directives,
        )
        schema = graph.schema
        compiler: _Compiler = GraphCompiler(graph)
      else:
        schema = build_schema("type Query { _micro: Boolean }")
        compiler = _UnavailableCompiler()
    except Exception as exc:
      self._composition_error = str(exc)
      raise
    self._runtime = _StoreRuntime(schema, compiler, module_ids)
    self._topology_revision = topology.revision
    self._composition_error = None
    self._graph_available = True

  @property
  def active_modules(self) -> tuple[str, ...]:
    return self._runtime.module_ids

  @property
  def topology_revision(self) -> int:
    return self._topology_revision

  @property
  def desired_topology_revision(self) -> int:
    return self._desired_topology_revision

  @property
  def composition_error(self) -> str | None:
    return self._composition_error

  @staticmethod
  def _is_introspection(operation: OperationDefinitionNode) -> bool:
    return bool(operation.selection_set.selections) and all(
      isinstance(selection, FieldNode) and selection.name.value.startswith("__")
      for selection in operation.selection_set.selections
    )

  @staticmethod
  def _errors(message: str, *, status_code: int) -> JSONResponse:
    return JSONResponse({"errors": [{"message": message}]}, status_code=status_code)

  def _unavailable(self) -> JSONResponse:
    error: dict[str, Any] = {
      "message": "Store graph is unavailable.",
      "desiredRevision": self._desired_topology_revision,
    }
    if self._composition_error is not None:
      error["detail"] = self._composition_error
    return JSONResponse({"errors": [error]}, status_code=503)
