from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Literal, Protocol

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
from pydantic import BaseModel, ConfigDict, Field, JsonValue, ValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse, Response

from micro._microservices import (
  BackendExecutionError,
  Microservice,
  request_content_type,
)

from ._module import GraphModule
from .composer import DirectiveMetadata, TypeDirectiveMetadata

type ResultShaper = Callable[[GraphBatchResult], Mapping[str, JsonValue]]


class StoreTopology(BaseModel):
  """The overseer-controlled module set exposed by a store instance."""

  model_config = ConfigDict(extra="forbid", frozen=True)

  revision: int = Field(ge=0)
  modules: tuple[GraphModule, ...]


class _GraphQLBody(BaseModel):
  query: str
  variables: dict[str, JsonValue] | None = None
  operation_name: str | None = Field(None, alias="operationName")


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
class GraphBatch:
  """Graph statements executed atomically and in order."""

  statements: tuple[GraphStatement, ...]

  def __post_init__(self) -> None:
    if not self.statements:
      raise ValueError("A graph batch needs at least one statement.")


@dataclass(frozen=True, slots=True)
class GraphBatchResult:
  results: tuple[GraphResult, ...]

  def __post_init__(self) -> None:
    if not self.results:
      raise ValueError("A graph batch result needs at least one result.")


@dataclass(frozen=True, slots=True)
class GraphEntityLayout:
  """Stable physical storage allocated for one composed GraphQL entity."""

  name: str
  label: str
  identity_property: str
  keys: tuple[tuple[str, ...], ...]


@dataclass(frozen=True, slots=True)
class GraphLayout:
  """Additive physical layout required by a composed graph revision."""

  revision: int
  entities: tuple[GraphEntityLayout, ...]


class GraphBackendError(GraphQLError, BackendExecutionError):
  """A stable, backend-neutral failure returned by a graph executor."""

  def __init__(
    self,
    message: str,
    *,
    code: Literal["CONFLICT", "UNAVAILABLE", "INVALID", "INTERNAL"],
    retryable: bool = False,
  ) -> None:
    super().__init__(
      message,
      extensions={"code": code, "retryable": retryable},
    )


@dataclass(frozen=True, slots=True)
class GraphQLRequest:
  schema: GraphQLSchema
  document: DocumentNode
  operation: OperationDefinitionNode
  variables: Mapping[str, Any]
  operation_name: str | None


@dataclass(frozen=True, slots=True)
class CompiledOperation:
  batch: GraphBatch
  shape: ResultShaper


class _Compiler(Protocol):
  def compile(self, request: GraphQLRequest) -> CompiledOperation: ...


class _UnavailableCompiler:
  def compile(self, request: GraphQLRequest) -> CompiledOperation:
    raise GraphQLError("The selected field has no active GraphQL module.")


class GraphExecutor(Protocol):
  async def start(self) -> None: ...

  async def execute(self, batch: GraphBatch) -> GraphBatchResult: ...

  async def apply_layout(self, layout: GraphLayout) -> None: ...

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
    if request_content_type(request) != "application/json":
      return self._errors("GraphQL requests require application/json.", status_code=415)

    try:
      body = _GraphQLBody.model_validate_json(await request.body())
    except ValidationError as exc:
      return JSONResponse(
        {"errors": [{"message": "Invalid GraphQL request.", "detail": str(exc)}]},
        status_code=400,
      )

    runtime = self._runtime
    try:
      document = parse(body.query)
    except GraphQLSyntaxError as exc:
      return JSONResponse({"errors": [exc.formatted]}, status_code=400)
    if errors := validate(runtime.schema, document):
      return JSONResponse(
        {"errors": [error.formatted for error in errors]}, status_code=400
      )
    operation = get_operation_ast(document, body.operation_name)
    if operation is None:
      return self._errors("GraphQL operation could not be selected.", status_code=400)

    coerced = get_variable_values(
      runtime.schema,
      operation.variable_definitions or (),
      body.variables or {},
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
        operation_name=body.operation_name,
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
      body.operation_name,
    )
    try:
      compiled = runtime.compiler.compile(graphql_request)
      result = await self.executor.execute(compiled.batch)
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
    if request_content_type(request) != "application/json":
      return self._errors("Store topology requires application/json.", status_code=415)
    try:
      topology = StoreTopology.model_validate_json(await request.body())
      await self.apply_topology(topology)
    except (GraphQLError, TypeError, ValueError) as exc:
      return JSONResponse(
        {"errors": [{"message": "Store topology was rejected.", "detail": str(exc)}]},
        status_code=409,
      )
    return Response(status_code=204)

  async def apply_topology(self, topology: StoreTopology) -> None:
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
        from ._compiler import GraphCompiler, physical_type
        from .composer import compose_graph

        graph = compose_graph(
          topology.modules,
          directives=self._directives,
          type_directives=self._type_directives,
        )
        schema = graph.schema
        compiler: _Compiler = GraphCompiler(graph)
        await self.executor.apply_layout(
          GraphLayout(
            topology.revision,
            tuple(
              GraphEntityLayout(
                entity.name,
                physical_type(entity.name),
                "_micro_id",
                entity.keys,
              )
              for entity in sorted(graph.entities.values(), key=lambda item: item.name)
            ),
          )
        )
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
