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
from pydantic import BaseModel, ConfigDict, Field, JsonValue

from micro.errors import BackendExecutionError

from ._module import GraphModule
from .composer import DirectiveMetadata, TypeDirectiveMetadata

type ResultShaper = Callable[[GraphBatchResult], Mapping[str, JsonValue]]


class GraphQLBody(BaseModel):
  """A GraphQL operation sent to the store."""

  model_config = ConfigDict(populate_by_name=True)

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
    problem = _validated(self.text)
    if problem is not None:
      raise ValueError(f"Graph statement is not valid ISO GQL: {problem}")
    if len(set(self.columns)) != len(self.columns) or any(
      not column.isidentifier() for column in self.columns
    ):
      raise ValueError("Graph result columns must be unique identifiers.")
    object.__setattr__(self, "parameters", MappingProxyType(dict(self.parameters)))


_VALIDATED: dict[str, str | None] = {}
"""Validation results per statement text: queries repeat with new parameters."""


def _validated(text: str) -> str | None:
  if text not in _VALIDATED:
    validation = Dialect.get_or_raise("fullgql").validate(text)
    _VALIDATED[text] = (
      None
      if validation.success
      else "; ".join(str(item) for item in validation.diagnostics)
    )
  return _VALIDATED[text]


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
class _Composition:
  schema: GraphQLSchema
  compiler: _Compiler
  module_ids: tuple[str, ...]
  documents: dict[str, tuple[DocumentNode | None, list[Any]]] = field(
    default_factory=dict
  )


class GraphEngine:
  """Composes graph modules and executes GraphQL against a graph executor."""

  def __init__(
    self,
    executor: GraphExecutor,
    *,
    directives: Sequence[DirectiveMetadata] = (),
    type_directives: Sequence[TypeDirectiveMetadata] = (),
  ) -> None:
    self.executor = executor
    self._directives = tuple(directives)
    self._type_directives = tuple(type_directives)
    self._composition = _Composition(
      build_schema("type Query { _micro: Boolean }"), _UnavailableCompiler(), ()
    )
    self._revision = 0
    self._available = True
    self._error: str | None = None
    self._signature = ""

  @property
  def available(self) -> bool:
    return self._available

  @property
  def active_modules(self) -> tuple[str, ...]:
    return self._composition.module_ids

  @property
  def revision(self) -> int:
    return self._revision

  @property
  def composition_error(self) -> str | None:
    return self._error

  @property
  def schema(self) -> GraphQLSchema:
    return self._composition.schema

  async def apply_modules(self, modules: Sequence[GraphModule]) -> None:
    """Compose a module set and evolve the physical layout additively."""
    ordered = tuple(sorted(modules, key=lambda module: module.id))
    module_ids = tuple(module.id for module in ordered)
    if len(set(module_ids)) != len(module_ids):
      raise ValueError("Graph modules contain duplicate IDs.")
    if (
      module_ids == self._composition.module_ids
      and self._error is None
      and self._signature == _signature(ordered)
    ):
      return
    revision = self._revision + 1
    try:
      if ordered:
        from ._compiler import GraphCompiler, physical_type
        from .composer import compose_graph

        graph = compose_graph(
          ordered,
          directives=self._directives,
          type_directives=self._type_directives,
        )
        schema = graph.schema
        compiler: _Compiler = GraphCompiler(graph)
        await self.executor.apply_layout(
          GraphLayout(
            revision,
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
      # Keep serving the last good composition; report why the new one failed.
      self._error = str(exc)
      raise
    self._composition = _Composition(schema, compiler, module_ids)
    self._signature = _signature(ordered)
    self._revision = revision
    self._error = None
    self._available = True

  async def execute(self, body: GraphQLBody) -> dict[str, JsonValue]:
    """Run one operation; failures are GraphQL `errors`, never exceptions."""
    if not self._available:
      error: dict[str, JsonValue] = {"message": "Store graph is unavailable."}
      if self._error is not None:
        error["detail"] = self._error
      return {"data": None, "errors": [error]}
    composition = self._composition
    # Parsing and validation depend only on the query text and the graph, and
    # clients repeat the same queries with new variables.
    cached = composition.documents.get(body.query)
    if cached is None:
      try:
        parsed = parse(body.query)
        problems = [error.formatted for error in validate(composition.schema, parsed)]
      except GraphQLSyntaxError as exc:
        parsed, problems = None, [exc.formatted]
      cached = composition.documents[body.query] = (parsed, problems)
    document, problems = cached
    if problems or document is None:
      return {"data": None, "errors": problems}  # pyright: ignore[reportReturnType]
    operation = get_operation_ast(document, body.operation_name)
    if operation is None:
      return {
        "data": None,
        "errors": [{"message": "GraphQL operation could not be selected."}],
      }
    coerced = get_variable_values(
      composition.schema, operation.variable_definitions or (), body.variables or {}
    )
    if isinstance(coerced, list):
      return {"data": None, "errors": [error.formatted for error in coerced]}  # pyright: ignore[reportReturnType]
    if _is_introspection(operation):
      result = execute_sync(
        composition.schema,
        document,
        variable_values=coerced,
        operation_name=body.operation_name,
      )
      response: dict[str, JsonValue] = {"data": result.data}  # pyright: ignore[reportAssignmentType]
      if result.errors:
        response["errors"] = [error.formatted for error in result.errors]  # pyright: ignore[reportArgumentType]
      return response
    request = GraphQLRequest(
      composition.schema,
      document,
      operation,
      MappingProxyType(coerced),
      body.operation_name,
    )
    try:
      compiled = composition.compiler.compile(request)
      batch_result = await self.executor.execute(compiled.batch)
      data = dict(compiled.shape(batch_result))
    except GraphQLError as exc:
      return {"data": None, "errors": [exc.formatted]}  # pyright: ignore[reportReturnType]
    return {"data": data}

  def print_schema(self) -> str:
    return print_schema(self._composition.schema)


def _signature(modules: Sequence[GraphModule]) -> str:
  return "\0".join(f"{module.id}\0{module.graphql_schema}" for module in modules)


def _is_introspection(operation: OperationDefinitionNode) -> bool:
  return bool(operation.selection_set.selections) and all(
    isinstance(selection, FieldNode) and selection.name.value.startswith("__")
    for selection in operation.selection_set.selections
  )
