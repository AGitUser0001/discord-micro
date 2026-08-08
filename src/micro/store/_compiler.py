import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, cast

from graphql import (
  FieldNode,
  FragmentDefinitionNode,
  FragmentSpreadNode,
  GraphQLCompositeType,
  GraphQLError,
  GraphQLField,
  GraphQLIncludeDirective,
  GraphQLList,
  GraphQLNonNull,
  GraphQLObjectType,
  GraphQLSchema,
  GraphQLSkipDirective,
  GraphQLType,
  InlineFragmentNode,
  SelectionSetNode,
  do_types_overlap,
  get_argument_values,
  get_directive_values,
  get_named_type,
  is_composite_type,
  is_leaf_type,
)
from pydantic import JsonValue

from ._store import CompiledOperation, GraphQLRequest, GraphResult, GraphStatement
from .composer import DirectiveCompileContext, MicroGraph

_LAYOUT_VERSION = "micro:gql-layout:v1"
_IDENTIFIER = re.compile(r"[^A-Za-z0-9_]")


@dataclass(slots=True)
class _Projection:
  response_name: str
  identity_column: str
  scalar_fields: list[tuple[str, str]]
  object_fields: list[tuple[str, _Projection, bool]]


@dataclass(frozen=True, slots=True)
class _ScalarProjection:
  response_name: str
  column: str


@dataclass(frozen=True, slots=True)
class _RootObjectProjection:
  projection: _Projection
  is_list: bool


class GraphCompiler:
  """Compiles a composed Micro graph into canonical GQL."""

  def __init__(self, graph: MicroGraph) -> None:
    self.graph = graph

  def compile(self, request: GraphQLRequest) -> CompiledOperation:
    root_type = request.schema.get_root_type(request.operation.operation)
    if root_type is None:
      raise GraphQLError("The GraphQL operation has no root type.")
    fragments = {
      definition.name.value: definition
      for definition in request.document.definitions
      if isinstance(definition, FragmentDefinitionNode)
    }
    root_fields = _collect_fields(
      request.schema,
      root_type,
      request.operation.selection_set,
      fragments,
      request.variables,
    )
    parameters: dict[str, JsonValue] = {}
    clauses: list[str] = []
    returns: list[str] = []
    counters = {"node": 0, "column": 0, "parameter": 0}
    projections: list[_RootObjectProjection | _ScalarProjection] = []
    for root_field in root_fields:
      field_definition = root_type.fields[root_field.name.value]
      binding = self.graph.bindings.get((root_type.name, root_field.name.value))
      if binding is None:
        raise GraphQLError(
          f"Root field {root_field.name.value!r} has no runtime directive."
        )
      arguments = get_argument_values(
        field_definition,
        root_field,
        dict(request.variables),
      )
      variable = _node(counters)
      parameter_prefix = f"p{counters['parameter']}"
      counters["parameter"] += 1
      try:
        source = binding.directive.compile(
          DirectiveCompileContext(
            request.operation.operation,
            root_field.name.value,
            binding.return_type,
            arguments,
            variable,
            None,
            parameter_prefix,
            binding.value,
          )
        )
      except (TypeError, ValueError, NameError) as exc:
        raise GraphQLError(
          f"@{binding.directive.name} failed for {root_field.name.value!r}: {exc}"
        ) from exc
      overlap = set(parameters) & set(source.parameters)
      if overlap:
        raise GraphQLError(
          f"Runtime directive produced duplicate parameters: {', '.join(overlap)}."
        )
      parameters.update(source.parameters)
      clauses.extend(source.clauses)
      named = get_named_type(field_definition.type)
      if is_leaf_type(named):
        if source.value is None:
          raise GraphQLError(
            f"@{binding.directive.name} did not provide a scalar value expression."
          )
        column = _column(counters)
        returns.append(f"{source.value} AS {column}")
        projections.append(
          _ScalarProjection(
            root_field.alias.value if root_field.alias else root_field.name.value,
            column,
          )
        )
        continue
      if not isinstance(named, GraphQLObjectType):
        raise GraphQLError(
          f"Runtime field {root_field.name.value!r} must return an object."
        )
      projections.append(
        _RootObjectProjection(
          self._project_object(
            request,
            named,
            root_field,
            variable,
            source.path,
            fragments,
            clauses,
            parameters,
            returns,
            counters,
          ),
          _is_list(field_definition),
        )
      )
    if not returns:
      returns.append("0 AS _micro_empty")
    statement = GraphStatement(
      " ".join((*clauses, f"RETURN {', '.join(returns)}")),
      parameters,
      tuple(_return_columns(returns)),
    )

    def shape(result: GraphResult) -> Mapping[str, JsonValue]:
      return {
        (
          projection.projection.response_name
          if isinstance(projection, _RootObjectProjection)
          else projection.response_name
        ): (
          _shape_root_projection(projection, result.rows)
          if isinstance(projection, _RootObjectProjection)
          else (result.rows[0].get(projection.column) if result.rows else None)
        )
        for projection in projections
      }

    return CompiledOperation(statement, shape)

  def _project_object(
    self,
    request: GraphQLRequest,
    object_type: GraphQLObjectType,
    selection: FieldNode,
    variable: str,
    path: str,
    fragments: Mapping[str, FragmentDefinitionNode],
    clauses: list[str],
    parameters: dict[str, JsonValue],
    returns: list[str],
    counters: dict[str, int],
  ) -> _Projection:
    response_name = selection.alias.value if selection.alias else selection.name.value
    identity_column = _column(counters)
    returns.append(f"{variable}._micro_id AS {identity_column}")
    projection = _Projection(response_name, identity_column, [], [])
    if selection.selection_set is None:
      raise GraphQLError(f"Object field {response_name!r} requires a selection set.")

    children = _collect_fields(
      request.schema,
      object_type,
      selection.selection_set,
      fragments,
      request.variables,
    )
    for child in children:
      if child.name.value == "__typename":
        column = _column(counters)
        returns.append(f"'{object_type.name}' AS {column}")
        projection.scalar_fields.append(
          (child.alias.value if child.alias else "__typename", column)
        )
        continue
      definition = object_type.fields.get(child.name.value)
      if definition is None:
        raise GraphQLError(
          f"Type {object_type.name} has no field {child.name.value!r}."
        )
      child_name = child.alias.value if child.alias else child.name.value
      named = get_named_type(definition.type)
      binding = self.graph.bindings.get((object_type.name, child.name.value))
      if is_leaf_type(named):
        column = _column(counters)
        if binding is None:
          if child.arguments:
            raise GraphQLError(
              f"Scalar field {object_type.name}.{child.name.value} has arguments "
              "but no runtime directive."
            )
          coordinate = f"{path}.{child.name.value}"
          value = f"{variable}.{physical_field(coordinate)}"
        else:
          arguments = get_argument_values(
            definition,
            child,
            dict(request.variables),
          )
          prefix = f"p{counters['parameter']}"
          counters["parameter"] += 1
          source = binding.directive.compile(
            DirectiveCompileContext(
              request.operation.operation,
              child.name.value,
              binding.return_type,
              arguments,
              _node(counters),
              variable,
              prefix,
              binding.value,
            )
          )
          parameters.update(source.parameters)
          clauses.extend(source.clauses)
          if source.value is None:
            raise GraphQLError(
              f"@{binding.directive.name} did not provide a scalar value expression."
            )
          value = source.value
        returns.append(f"{value} AS {column}")
        projection.scalar_fields.append((child_name, column))
        continue
      if not isinstance(named, GraphQLObjectType):
        raise GraphQLError(
          f"Field {object_type.name}.{child.name.value} has an unsupported type."
        )
      node_variable = _node(counters)
      coordinate = f"{path}.{child.name.value}"
      child_path = named.name if named.name in self.graph.entities else coordinate
      child_label = (
        physical_type(named.name)
        if named.name in self.graph.entities
        else physical_path_type(named.name, child_path)
      )
      if binding is None:
        if child.arguments:
          raise GraphQLError(
            f"Nested field {object_type.name}.{child.name.value} has arguments "
            "but no runtime directive."
          )
        clauses.append(
          f"OPTIONAL MATCH ({variable})-[:{physical_reference(coordinate)}]->"
          f"({node_variable}:{child_label})"
        )
      else:
        arguments = get_argument_values(
          definition,
          child,
          dict(request.variables),
        )
        prefix = f"p{counters['parameter']}"
        counters["parameter"] += 1
        source = binding.directive.compile(
          DirectiveCompileContext(
            request.operation.operation,
            child.name.value,
            binding.return_type,
            arguments,
            node_variable,
            variable,
            prefix,
            binding.value,
          )
        )
        overlap = set(parameters) & set(source.parameters)
        if overlap:
          raise GraphQLError("A runtime directive produced duplicate parameters.")
        parameters.update(source.parameters)
        clauses.extend(source.clauses)
        child_path = source.path
      child_projection = self._project_object(
        request,
        named,
        child,
        node_variable,
        child_path,
        fragments,
        clauses,
        parameters,
        returns,
        counters,
      )
      projection.object_fields.append(
        (child_name, child_projection, _is_list(definition))
      )
    return projection


def physical_type(type_name: str) -> str:
  return _physical_name(type_name, "type", type_name)


def physical_reference(coordinate: str) -> str:
  return _physical_name(coordinate.rsplit(".", 1)[-1], "field", coordinate)


def physical_path_type(type_name: str, path: str) -> str:
  return _physical_name(type_name, "path-type", path)


def physical_field(coordinate: str) -> str:
  return _physical_name(coordinate.rsplit(".", 1)[-1], "property", coordinate)


def entity_identity(type_name: str, key: Mapping[str, object]) -> str:
  encoded = json.dumps(
    [_LAYOUT_VERSION, "entity", type_name, key],
    ensure_ascii=False,
    separators=(",", ":"),
    sort_keys=True,
  ).encode()
  return hashlib.sha256(encoded).hexdigest()


def _physical_name(readable: str, kind: str, coordinate: str) -> str:
  prefix = _IDENTIFIER.sub("_", readable)[:32].strip("_") or kind
  digest = hashlib.sha256(
    f"{_LAYOUT_VERSION}\0{kind}\0{coordinate}".encode()
  ).hexdigest()[:20]
  return f"{prefix}_{digest}"


def _column(counters: dict[str, int]) -> str:
  column = f"c{counters['column']}"
  counters["column"] += 1
  return column


def _node(counters: dict[str, int]) -> str:
  node = f"n{counters['node']}"
  counters["node"] += 1
  return node


def _collect_fields(
  schema: GraphQLSchema,
  object_type: GraphQLObjectType,
  selection_set: SelectionSetNode,
  fragments: Mapping[str, FragmentDefinitionNode],
  variables: Mapping[str, Any],
  visited: frozenset[str] = frozenset(),
) -> tuple[FieldNode, ...]:
  fields: dict[str, FieldNode] = {}

  def add(field: FieldNode) -> None:
    response_name = field.alias.value if field.alias else field.name.value
    previous = fields.get(response_name)
    if previous is None:
      fields[response_name] = field
      return
    selections = (
      *((previous.selection_set.selections) if previous.selection_set else ()),
      *((field.selection_set.selections) if field.selection_set else ()),
    )
    fields[response_name] = FieldNode(
      alias=previous.alias,
      name=previous.name,
      arguments=previous.arguments,
      directives=previous.directives,
      selection_set=SelectionSetNode(selections=selections) if selections else None,
    )

  for selection in selection_set.selections:
    if not _included(selection, variables):
      continue
    if isinstance(selection, FieldNode):
      add(selection)
      continue
    if isinstance(selection, FragmentSpreadNode):
      name = selection.name.value
      if name in visited:
        continue
      fragment = fragments[name]
      condition = schema.get_type(fragment.type_condition.name.value)
      if (
        condition is None
        or not is_composite_type(condition)
        or not do_types_overlap(
          schema, object_type, cast(GraphQLCompositeType, condition)
        )
      ):
        continue
      for field in _collect_fields(
        schema,
        object_type,
        fragment.selection_set,
        fragments,
        variables,
        visited | {name},
      ):
        add(field)
      continue
    if isinstance(selection, InlineFragmentNode):
      if selection.type_condition is not None:
        condition = schema.get_type(selection.type_condition.name.value)
        if (
          condition is None
          or not is_composite_type(condition)
          or not do_types_overlap(
            schema, object_type, cast(GraphQLCompositeType, condition)
          )
        ):
          continue
      for field in _collect_fields(
        schema,
        object_type,
        selection.selection_set,
        fragments,
        variables,
        visited,
      ):
        add(field)
  return tuple(fields.values())


def _included(node: Any, variables: Mapping[str, Any]) -> bool:
  skipped = get_directive_values(GraphQLSkipDirective, node, dict(variables))
  if skipped is not None and skipped["if"]:
    return False
  included = get_directive_values(GraphQLIncludeDirective, node, dict(variables))
  return included is None or bool(included["if"])


def _return_columns(returns: Sequence[str]) -> Sequence[str]:
  return tuple(item.rsplit(" AS ", 1)[1] for item in returns)


def _is_list(field: GraphQLField) -> bool:
  field_type: GraphQLType = field.type
  if isinstance(field_type, GraphQLNonNull):
    field_type = field_type.of_type
  return isinstance(field_type, GraphQLList)


def _shape_projection(
  projection: _Projection,
  rows: Sequence[Mapping[str, JsonValue]],
) -> JsonValue:
  present = [row for row in rows if row.get(projection.identity_column) is not None]
  if not present:
    return None
  first = present[0]
  result: dict[str, JsonValue] = {
    response_name: first.get(column)
    for response_name, column in projection.scalar_fields
  }
  for response_name, child, is_list in projection.object_fields:
    if is_list:
      groups: dict[str, list[Mapping[str, JsonValue]]] = {}
      for row in present:
        identity = row.get(child.identity_column)
        if isinstance(identity, str):
          groups.setdefault(identity, []).append(row)
      result[response_name] = [
        _shape_projection(child, grouped_rows) for grouped_rows in groups.values()
      ]
    else:
      result[response_name] = _shape_projection(child, present)
  return result


def _shape_root_projection(
  root: _RootObjectProjection,
  rows: Sequence[Mapping[str, JsonValue]],
) -> JsonValue:
  if not root.is_list:
    return _shape_projection(root.projection, rows)
  groups: dict[str, list[Mapping[str, JsonValue]]] = {}
  for row in rows:
    identity = row.get(root.projection.identity_column)
    if isinstance(identity, str):
      groups.setdefault(identity, []).append(row)
  return [
    _shape_projection(root.projection, grouped_rows) for grouped_rows in groups.values()
  ]
