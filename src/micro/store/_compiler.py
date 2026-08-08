import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import cast

from graphql import (
  FieldNode,
  GraphQLError,
  GraphQLField,
  GraphQLList,
  GraphQLNonNull,
  GraphQLObjectType,
  GraphQLType,
  get_argument_values,
  get_named_type,
  is_leaf_type,
)
from pydantic import JsonValue

from ._store import CompiledOperation, GraphQLRequest, GraphResult, GraphStatement
from .composer import MicroGraph

_LAYOUT_VERSION = "micro:gql-layout:v1"
_IDENTIFIER = re.compile(r"[^A-Za-z0-9_]")


@dataclass(slots=True)
class _Projection:
  response_name: str
  identity_column: str
  scalar_fields: list[tuple[str, str]]
  object_fields: list[tuple[str, _Projection, bool]]


class MicroGraphCompiler:
  """Compiles a composed Micro graph into canonical GQL."""

  def __init__(self, graph: MicroGraph) -> None:
    self.graph = graph

  def compile(self, request: GraphQLRequest) -> CompiledOperation:
    selections = request.operation.selection_set.selections
    if len(selections) != 1 or not isinstance(selections[0], FieldNode):
      raise GraphQLError("A compiled store operation requires one root field.")
    root_field = selections[0]
    lookup = self.graph.lookups.get(
      (request.operation.operation, root_field.name.value)
    )
    if lookup is None:
      raise GraphQLError(
        f"Root field {root_field.name.value!r} has no Micro runtime macro."
      )

    root_type = request.schema.get_root_type(request.operation.operation)
    if root_type is None:
      raise GraphQLError("The GraphQL operation has no root type.")
    field_definition = root_type.fields[root_field.name.value]
    arguments = get_argument_values(
      field_definition,
      root_field,
      dict(request.variables),
    )
    try:
      key = lookup.expression.evaluate(arguments)
    except (TypeError, ValueError, NameError) as exc:
      raise GraphQLError(
        f"The @from expression for {root_field.name.value!r} failed: {exc}"
      ) from exc
    parameters: dict[str, JsonValue] = {
      "root_identity": entity_identity(lookup.entity.name, key)
    }
    matches = [
      f"MATCH (n0:{physical_type(lookup.entity.name)})",
      "WHERE n0._micro_id = $root_identity",
    ]
    returns: list[str] = []
    counters = {"node": 1, "column": 0}
    root_projection = self._project_object(
      cast(GraphQLObjectType, get_named_type(field_definition.type)),
      root_field,
      "n0",
      lookup.entity.name,
      matches,
      returns,
      counters,
    )
    if not returns:
      raise GraphQLError("A compiled store query must select at least one field.")
    statement = GraphStatement(
      " ".join((*matches, f"RETURN {', '.join(returns)}")),
      parameters,
      tuple(_return_columns(returns)),
    )

    def shape(result: GraphResult) -> Mapping[str, JsonValue]:
      value = _shape_projection(root_projection, result.rows)
      return {root_projection.response_name: value}

    return CompiledOperation(statement, shape)

  def _project_object(
    self,
    object_type: GraphQLObjectType,
    selection: FieldNode,
    variable: str,
    path: str,
    matches: list[str],
    returns: list[str],
    counters: dict[str, int],
  ) -> _Projection:
    response_name = selection.alias.value if selection.alias else selection.name.value
    identity_column = _column(counters)
    returns.append(f"{variable}._micro_id AS {identity_column}")
    projection = _Projection(response_name, identity_column, [], [])
    if selection.selection_set is None:
      raise GraphQLError(f"Object field {response_name!r} requires a selection set.")

    for child in selection.selection_set.selections:
      if not isinstance(child, FieldNode):
        raise GraphQLError("Fragments are not supported by the GQL compiler yet.")
      if child.arguments:
        raise GraphQLError("Nested field arguments are not supported yet.")
      definition = object_type.fields.get(child.name.value)
      if definition is None:
        raise GraphQLError(
          f"Type {object_type.name} has no field {child.name.value!r}."
        )
      child_name = child.alias.value if child.alias else child.name.value
      named = get_named_type(definition.type)
      if is_leaf_type(named):
        column = _column(counters)
        coordinate = f"{path}.{child.name.value}"
        returns.append(f"{variable}.{physical_field(coordinate)} AS {column}")
        projection.scalar_fields.append((child_name, column))
        continue
      if not isinstance(named, GraphQLObjectType):
        raise GraphQLError(
          f"Field {object_type.name}.{child.name.value} has an unsupported type."
        )
      node_variable = f"n{counters['node']}"
      counters["node"] += 1
      coordinate = f"{path}.{child.name.value}"
      child_path = named.name if named.name in self.graph.entities else coordinate
      child_label = (
        physical_type(named.name)
        if named.name in self.graph.entities
        else physical_path_type(named.name, child_path)
      )
      matches.append(
        f"OPTIONAL MATCH ({variable})-[:{physical_reference(coordinate)}]->"
        f"({node_variable}:{child_label})"
      )
      child_projection = self._project_object(
        named,
        child,
        node_variable,
        child_path,
        matches,
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
