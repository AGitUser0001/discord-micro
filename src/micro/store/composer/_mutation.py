import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Literal, cast

from graphglot import ast
from graphglot.dialect import Dialect
from graphql import EnumValueNode, ObjectValueNode, OperationType, StringValueNode
from pydantic import JsonValue

from ._composer import (
  Entity,
  GraphCompositionError,
  KeyBinding,
  _compile_key,
  _is_list_type,
  check_map,
)

_GQL = Dialect.get_or_raise("fullgql")


@dataclass(frozen=True, slots=True)
class GQLExpression:
  tree: Any
  parameters: frozenset[str]
  merge: tuple[str, str] | None = None
  """`current.f + $p` / `current.f - $p` as (operator, parameter): a map merge when `p`
  is an object (or, for `-`, a key or list of keys), done by Micro, not the backend."""

  def render(
    self,
    entity: Entity,
    variable: str,
    parameter_prefix: str,
    arguments: dict[str, object],
  ) -> tuple[str, dict[str, JsonValue]]:
    from .._compiler import physical_field

    tree = self.tree.deep_copy()
    for node in tree.dfs():
      if isinstance(node, ast.PropertyReference):
        source_reference = node.property_source
        if not isinstance(source_reference, ast.BindingVariableReference):
          raise TypeError("Validated GQL property source changed unexpectedly.")
        source_reference.binding_variable.name = variable
        field = node.property_name[0].identifier
        field.name = physical_field(f"{entity.name}.{field.name}")
      elif isinstance(node, ast.GeneralParameterReference):
        name = node.parameter_name.name
        node.parameter_name.name = f"{parameter_prefix}_{name}"
    rendered = _GQL.generate(tree)
    if not rendered.startswith("RETURN "):
      raise TypeError("GQL expression wrapper was not preserved.")
    return rendered.removeprefix("RETURN "), {
      f"{parameter_prefix}_{name}": arguments.get(name)  # type: ignore[dict-item]
      for name in self.parameters
    }


_FIELD = re.compile(r"\bcurrent\.([A-Za-z_][A-Za-z0-9_]*)")
_LITERAL = re.compile(r"('(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\")")


def _quote_fields(source: str) -> str:
  """Backtick each `current.field`, so a field may share a GQL keyword's name (`count`,
  `value`, `type`, ...). String literals are left as they are."""
  return "".join(
    part if index % 2 else _FIELD.sub(r"current.`\1`", part)
    for index, part in enumerate(_LITERAL.split(source))
  )


def compile_gql_expression(
  source: str, entity: Entity, arguments: set[str]
) -> GQLExpression:
  try:
    tree = _GQL.parse(f"RETURN {_quote_fields(source)}")[0]
  except Exception as exc:
    raise GraphCompositionError(f"Invalid GQL expression: {exc}") from exc
  parameters: set[str] = set()
  properties: set[str] = set()
  for node in tree.dfs():
    if isinstance(node, ast.PropertyReference):
      property_source = node.property_source
      if (
        not isinstance(property_source, ast.BindingVariableReference)
        or property_source.binding_variable.name != "current"
        or len(node.property_name) != 1
      ):
        raise GraphCompositionError(
          "GQL expressions may reference properties through current only."
        )
      properties.add(node.property_name[0].identifier.name)
    elif isinstance(node, ast.GeneralParameterReference):
      parameters.add(node.parameter_name.name)
  if unknown := properties - entity.fields:
    raise GraphCompositionError(
      f"GQL expression references unknown fields: {', '.join(sorted(unknown))}."
    )
  if unknown := parameters - arguments:
    raise GraphCompositionError(
      f"GQL expression references unknown arguments: {', '.join(sorted(unknown))}."
    )
  merge = _MERGE.fullmatch(source)
  return GQLExpression(
    tree,
    frozenset(parameters),
    None if merge is None else (merge.group(1), merge.group(2)),
  )


_MERGE = re.compile(
  r"\s*current\.`?[A-Za-z_][A-Za-z0-9_]*`?\s*([+-])\s*\$([A-Za-z_][A-Za-z0-9_]*)\s*"
)


def merge_map(current: object, operator: str, operand: object) -> dict[str, JsonValue]:
  """A map with `operand`'s entries set (`+`) or its keys removed (`-`); a missing map
  counts as empty."""
  merged: dict[str, JsonValue] = dict(current) if isinstance(current, dict) else {}  # pyright: ignore[reportUnknownArgumentType]
  if operator == "+":
    merged.update(cast(dict[str, JsonValue], operand))
  else:
    for key in [operand] if isinstance(operand, str) else cast(list[str], operand):
      merged.pop(key, None)
  return merged


def _is_merge(
  expression: GQLExpression | None, arguments: Mapping[str, object]
) -> bool:
  if expression is None or expression.merge is None:
    return False
  operator, name = expression.merge
  operand = arguments.get(name)
  return (
    isinstance(operand, dict) if operator == "+" else isinstance(operand, str | list)
  )


@dataclass(frozen=True, slots=True)
class Assignment:
  field: str
  argument: str | None = None
  expression: GQLExpression | None = None


from ._directive import (
  DirectiveBindContext,
  DirectiveCompileContext,
  DirectiveMetadata,
  DirectiveRead,
  DirectiveResult,
)


@dataclass(frozen=True, slots=True)
class EntityMutation:
  action: Literal["insert", "update", "upsert"]
  entity: Entity
  key: KeyBinding
  assignments: tuple[Assignment, ...]
  where: GQLExpression | None
  defaults: tuple[Assignment, ...] = ()
  """`@upsert`'s `insert`: what a missing entity is created with, besides its key."""


@dataclass(frozen=True, slots=True)
class DeleteMutation:
  entity: Entity
  key: KeyBinding


@dataclass(frozen=True, slots=True)
class RelationshipMutation:
  action: Literal["connect", "disconnect"]
  source: Entity
  source_key: KeyBinding
  target: Entity
  target_key: KeyBinding
  field: str
  edge: KeyBinding | None = None
  """Properties of the edge itself, each named after the argument that supplies it."""


def _directive_argument(context: DirectiveBindContext, name: str):
  directive = next(
    item
    for item in context.field.directives or ()
    if item.name.value
    in {"insert", "update", "upsert", "delete", "connect", "disconnect"}
  )
  argument = next(
    (item for item in directive.arguments or () if item.name.value == name),
    None,
  )
  if argument is None:
    raise GraphCompositionError(f"@{directive.name.value} requires {name}.")
  return argument.value


def _mutation_arguments(context: DirectiveBindContext) -> set[str]:
  return {argument.name.value for argument in context.field.arguments or ()}


def _require_mutation(context: DirectiveBindContext, name: str) -> None:
  if context.operation is not OperationType.MUTATION:
    raise GraphCompositionError(f"@{name} supports Mutation fields only.")
  if _is_list_type(context.field.type):
    raise GraphCompositionError(f"@{name} does not support list return types.")


def _assignments(
  value: object, action: str, name: str, entity: Entity, arguments: set[str]
) -> tuple[Assignment, ...]:
  """The `{field: argument or "GQL"}` object of a directive's `set` (or `insert`)."""
  if not isinstance(value, ObjectValueNode) or not value.fields:
    raise GraphCompositionError(f"@{action} {name} must be a non-empty object.")
  assignments: list[Assignment] = []
  for field in value.fields:
    if isinstance(field.value, EnumValueNode):
      if field.value.value not in arguments:
        raise GraphCompositionError(
          f"@{action} references unknown argument {field.value.value!r}."
        )
      assignments.append(Assignment(field.name.value, argument=field.value.value))
    elif isinstance(field.value, StringValueNode):
      assignments.append(
        Assignment(
          field.name.value,
          expression=compile_gql_expression(field.value.value, entity, arguments),
        )
      )
    else:
      raise GraphCompositionError(
        f"@{action} {name} values must be argument names or GQL strings."
      )
  unknown = {assignment.field for assignment in assignments} - entity.fields
  if unknown:
    raise GraphCompositionError(
      f"@{action} references unknown fields: {', '.join(sorted(unknown))}."
    )
  return tuple(assignments)


def _optional_argument(context: DirectiveBindContext, action: str, name: str):
  directive = next(
    item for item in context.field.directives or () if item.name.value == action
  )
  argument = next(
    (item for item in directive.arguments or () if item.name.value == name), None
  )
  return None if argument is None else argument.value


def _attach_entity_mutation(
  context: DirectiveBindContext,
  action: Literal["insert", "update"],
) -> EntityMutation:
  _require_mutation(context, action)
  if not isinstance(context.entity, Entity):
    raise GraphCompositionError(f"@{action} must return an @entity type.")
  arguments = _mutation_arguments(context)
  key = _compile_key(_directive_argument(context, "key"), arguments, action)
  assignments = _assignments(
    _directive_argument(context, "set"), action, "set", context.entity, arguments
  )
  if key.key_fields not in context.entity.keys:
    raise GraphCompositionError(f"@{action} key does not match an @entity key.")
  if action == "insert" and not set(key.key_fields) <= {
    assignment.field for assignment in assignments
  }:
    raise GraphCompositionError("@insert set must include every entity key field.")
  directive = next(
    item for item in context.field.directives or () if item.name.value == action
  )
  where_argument = next(
    (item for item in directive.arguments or () if item.name.value == "where"), None
  )
  where = None
  if where_argument is not None:
    if action != "update" or not isinstance(where_argument.value, StringValueNode):
      raise GraphCompositionError("@update where must be a GQL string.")
    where = compile_gql_expression(
      where_argument.value.value, context.entity, arguments
    )
  return EntityMutation(action, context.entity, key, tuple(assignments), where)


def _attach_upsert(context: DirectiveBindContext) -> EntityMutation:
  _require_mutation(context, "upsert")
  if not isinstance(context.entity, Entity):
    raise GraphCompositionError("@upsert must return an @entity type.")
  arguments = _mutation_arguments(context)
  key = _compile_key(_directive_argument(context, "key"), arguments, "upsert")
  if key.key_fields not in context.entity.keys:
    raise GraphCompositionError("@upsert key does not match an @entity key.")
  insert = _optional_argument(context, "upsert", "insert")
  defaults = (
    ()
    if insert is None
    else _assignments(insert, "upsert", "insert", context.entity, arguments)
  )
  if set(key.key_fields) & {item.field for item in defaults}:
    raise GraphCompositionError(
      "@upsert insert must not set key fields: they come from key."
    )
  update = _optional_argument(context, "upsert", "set")
  assignments = (
    ()
    if update is None
    else _assignments(update, "upsert", "set", context.entity, arguments)
  )
  return EntityMutation("upsert", context.entity, key, assignments, None, defaults)


def _attach_insert(context: DirectiveBindContext) -> EntityMutation:
  return _attach_entity_mutation(context, "insert")


def _attach_update(context: DirectiveBindContext) -> EntityMutation:
  return _attach_entity_mutation(context, "update")


def _render(
  entity: Entity,
  assignments: Sequence[Assignment],
  arguments: Mapping[str, object],
  variable: str,
  prefix: str,
  parameters: dict[str, JsonValue],
  merges: list[tuple[str, str, str, object]],
) -> list[tuple[str, str]]:
  """Each assignment as (physical field, GQL value), adding its parameters. A map merge
  becomes a parameter (physical field, parameter, operator, operand) in `merges`, for the
  caller to compute from the stored map."""
  from .._compiler import physical_field

  rendered: list[tuple[str, str]] = []
  for assignment in assignments:
    physical = physical_field(f"{entity.name}.{assignment.field}")
    if _is_merge(assignment.expression, arguments):
      assert (
        assignment.expression is not None and assignment.expression.merge is not None
      )
      operator, name = assignment.expression.merge
      check_map(entity, assignment.field, arguments[name])
      parameter = f"{prefix}_merged_{assignment.field}"
      merges.append((physical, parameter, operator, arguments[name]))
      rendered.append((physical, f"${parameter}"))
      continue
    if assignment.argument is not None:
      if assignment.argument not in arguments:
        continue  # not passed: an insert leaves it unset, an update leaves it as it is
      check_map(entity, assignment.field, arguments[assignment.argument])
      parameter = f"{prefix}_{assignment.argument}"
      parameters[parameter] = cast(JsonValue, arguments[assignment.argument])
      value = f"${parameter}"
    else:
      assert assignment.expression is not None
      for name in assignment.expression.parameters:  # `current.f + $patch`, `- $keys`
        check_map(entity, assignment.field, arguments.get(name))
      value, expression_parameters = assignment.expression.render(
        entity, variable, prefix, dict(arguments)
      )
      parameters.update(expression_parameters)
    rendered.append((physical, value))
  return rendered


def _compile_entity_mutation(context: DirectiveCompileContext) -> DirectiveResult:
  from .._compiler import entity_identity, physical_field, physical_type

  binding = context.binding
  if not isinstance(binding, EntityMutation):
    raise TypeError("Entity mutation received invalid attached metadata.")
  key = binding.key.evaluate(context.arguments)
  identity_parameter = f"{context.parameter_prefix}_identity"
  identity = entity_identity(binding.entity.name, key)
  parameters: dict[str, JsonValue] = {identity_parameter: identity}
  merges: list[tuple[str, str, str, object]] = []
  rendered = _render(
    binding.entity,
    binding.assignments,
    context.arguments,
    context.variable,
    context.parameter_prefix,
    parameters,
    merges,
  )
  reads: tuple[DirectiveRead, ...] = ()
  if merges and binding.action == "insert":  # nothing stored yet: merge into empty
    for _, parameter, operator, operand in merges:
      parameters[parameter] = merge_map(None, operator, operand)
  elif merges:  # read the stored maps, merge here, write the result
    read_parameter = f"{context.parameter_prefix}_read_identity"
    columns = tuple(f"m{index}" for index in range(len(merges)))
    found = list(zip(columns, merges, strict=True))

    def then(row: Mapping[str, JsonValue] | None) -> Mapping[str, JsonValue]:
      return {
        parameter: merge_map(
          None if row is None else row.get(column), operator, operand
        )
        for column, (_, parameter, operator, operand) in found
      }

    reads = (
      DirectiveRead(
        f"MATCH (n:{physical_type(binding.entity.name)}) "
        f"WHERE n._micro_id = ${read_parameter} RETURN "
        + ", ".join(f"n.{physical} AS {column}" for column, (physical, *_) in found),
        {read_parameter: identity},
        columns,
        then,
      ),
    )
  properties = [f"_micro_id: ${identity_parameter}"]
  properties += [f"{physical}: {value}" for physical, value in rendered]
  assignments = [
    f"{context.variable}.{physical} = {value}" for physical, value in rendered
  ]
  before: tuple[tuple[str, Mapping[str, JsonValue]], ...] = ()
  if binding.action == "upsert":
    # ISO GQL has no MERGE: a statement ahead of the operation, in the same
    # transaction, creates the entity when it is missing; the field is then an update.
    created = f"{context.variable}_new"
    prefix = f"{context.parameter_prefix}_insert"
    insert_parameters: dict[str, JsonValue] = {f"{prefix}_identity": identity}
    for field_name, value in key.items():
      insert_parameters[f"{prefix}_key_{field_name}"] = cast(JsonValue, value)
    values = [
      (physical_field(f"{binding.entity.name}.{name}"), f"${prefix}_key_{name}")
      for name in key
    ] + _render(
      binding.entity,
      binding.defaults,
      context.arguments,
      context.variable,
      prefix,
      insert_parameters,
      created_merges := [],
    )
    for _, parameter, operator, operand in created_merges:
      insert_parameters[parameter] = merge_map(None, operator, operand)
    inserted = ", ".join(
      [f"_micro_id: ${prefix}_identity"] + [f"{p}: {v}" for p, v in values]
    )
    entity_type = physical_type(binding.entity.name)
    before = (
      (
        " ".join(
          (
            f"OPTIONAL MATCH ({context.variable}:{entity_type})",
            f"WHERE {context.variable}._micro_id = ${prefix}_identity",
            f"FILTER {context.variable} IS NULL",
            f"INSERT ({created}:{entity_type} {{{inserted}}})",
          )
        ),
        insert_parameters,
      ),
    )
  if binding.action == "insert":
    clauses = (
      (
        f"INSERT ({context.variable}:{physical_type(binding.entity.name)} "
        f"{{{', '.join(properties)}}})"
      ),
    )
  else:
    clauses_list = [
      f"MATCH ({context.variable}:{physical_type(binding.entity.name)})",
      f"WHERE {context.variable}._micro_id = ${identity_parameter}",
    ]
    if binding.where is not None:
      where, where_parameters = binding.where.render(
        binding.entity,
        context.variable,
        context.parameter_prefix,
        dict(context.arguments),
      )
      parameters.update(where_parameters)
      clauses_list[-1] += f" AND ({where})"
    if assignments:
      clauses_list.append(f"SET {', '.join(assignments)}")
    clauses = tuple(clauses_list)
  return DirectiveResult(
    clauses,
    parameters,
    binding.entity.name,
    before=before,
    reads=reads,
  )


def _attach_delete(context: DirectiveBindContext) -> DeleteMutation:
  _require_mutation(context, "delete")
  entity_name_value = _directive_argument(context, "type")
  if not isinstance(entity_name_value, StringValueNode):
    raise GraphCompositionError("@delete type must be a string.")
  entity_name = entity_name_value.value
  entity = context.entities.get(entity_name)
  if not isinstance(entity, Entity):
    raise GraphCompositionError(f"@delete references unknown entity {entity_name!r}.")
  key = _compile_key(
    _directive_argument(context, "key"), _mutation_arguments(context), "delete"
  )
  if key.key_fields not in entity.keys:
    raise GraphCompositionError("@delete key does not match an @entity key.")
  return DeleteMutation(entity, key)


def _compile_delete(context: DirectiveCompileContext) -> DirectiveResult:
  from .._compiler import entity_identity, physical_type

  binding = context.binding
  if not isinstance(binding, DeleteMutation):
    raise TypeError("@delete received invalid attached metadata.")
  parameter = f"{context.parameter_prefix}_identity"
  return DirectiveResult(
    (
      f"MATCH ({context.variable}:{physical_type(binding.entity.name)})",
      f"WHERE {context.variable}._micro_id = ${parameter}",
      f"DETACH DELETE {context.variable}",
    ),
    {
      parameter: entity_identity(
        binding.entity.name, binding.key.evaluate(context.arguments)
      )
    },
    "",
    "true",
  )


def _attach_relationship(
  context: DirectiveBindContext,
  action: Literal["connect", "disconnect"],
) -> RelationshipMutation:
  _require_mutation(context, action)
  source_name_value = _directive_argument(context, "fromType")
  target_name_value = _directive_argument(context, "toType")
  if not isinstance(source_name_value, StringValueNode) or not isinstance(
    target_name_value, StringValueNode
  ):
    raise GraphCompositionError(f"@{action} entity types must be strings.")
  source_name = source_name_value.value
  target_name = target_name_value.value
  source = context.entities.get(source_name)
  target = context.entities.get(target_name)
  if not isinstance(source, Entity) or not isinstance(target, Entity):
    raise GraphCompositionError(f"@{action} references an unknown entity type.")
  field_value = _directive_argument(context, "field")
  if not isinstance(field_value, StringValueNode):
    raise GraphCompositionError(f"@{action} field must be a string.")
  field = field_value.value
  if field not in source.fields:
    raise GraphCompositionError(
      f"@{action} references unknown field {source.name}.{field}."
    )
  arguments = _mutation_arguments(context)
  source_key = _compile_key(_directive_argument(context, "fromKey"), arguments, action)
  target_key = _compile_key(_directive_argument(context, "toKey"), arguments, action)
  if (
    source_key.key_fields not in source.keys or target_key.key_fields not in target.keys
  ):
    raise GraphCompositionError(f"@{action} key does not match an @entity key.")
  directive = next(
    item for item in context.field.directives or () if item.name.value == action
  )
  edge_argument = next(
    (item for item in directive.arguments or () if item.name.value == "edge"), None
  )
  edge = (
    _compile_key(edge_argument.value, arguments, action)
    if edge_argument is not None
    else None
  )
  return RelationshipMutation(
    action, source, source_key, target, target_key, field, edge
  )


def _attach_connect(context: DirectiveBindContext) -> RelationshipMutation:
  return _attach_relationship(context, "connect")


def _attach_disconnect(context: DirectiveBindContext) -> RelationshipMutation:
  return _attach_relationship(context, "disconnect")


def _compile_relationship(context: DirectiveCompileContext) -> DirectiveResult:
  from .._compiler import entity_identity, physical_reference, physical_type

  binding = context.binding
  if not isinstance(binding, RelationshipMutation):
    raise TypeError("Relationship mutation received invalid attached metadata.")
  source_parameter = f"{context.parameter_prefix}_from"
  target_parameter = f"{context.parameter_prefix}_to"
  source_variable = f"{context.variable}_from"
  target_variable = f"{context.variable}_to"
  relationship_variable = f"{context.variable}_relationship"
  relationship_type = physical_reference(f"{binding.source.name}.{binding.field}")
  clauses = [
    (
      f"MATCH ({source_variable}:{physical_type(binding.source.name)}), "
      f"({target_variable}:{physical_type(binding.target.name)})"
    ),
    (
      f"WHERE {source_variable}._micro_id = ${source_parameter} AND "
      f"{target_variable}._micro_id = ${target_parameter}"
    ),
  ]
  edge_parameters: dict[str, JsonValue] = {}
  edge_properties: list[str] = []
  edge_filters: list[str] = []
  for name, argument in binding.edge.fields if binding.edge is not None else ():
    parameter = f"{context.parameter_prefix}_edge_{name}"
    edge_parameters[parameter] = cast(JsonValue, context.arguments.get(argument))
    edge_properties.append(f"{name}: ${parameter}")
    edge_filters.append(f"{relationship_variable}.{name} = ${parameter}")
  if binding.action == "connect":
    properties = f" {{{', '.join(edge_properties)}}}" if edge_properties else ""
    clauses.append(
      f"INSERT ({source_variable})-[:{relationship_type}{properties}]->"
      f"({target_variable})"
    )
  else:
    clauses[0] = (
      f"MATCH ({source_variable}:{physical_type(binding.source.name)})-"
      f"[{relationship_variable}:{relationship_type}]->"
      f"({target_variable}:{physical_type(binding.target.name)})"
    )
    if edge_filters:  # only the entry under that key (and any other edge property)
      clauses[1] += " AND " + " AND ".join(edge_filters)
    clauses.append(f"DELETE {relationship_variable}")
  source_identity = entity_identity(
    binding.source.name, binding.source_key.evaluate(context.arguments)
  )
  target_identity = entity_identity(
    binding.target.name, binding.target_key.evaluate(context.arguments)
  )
  return DirectiveResult(
    tuple(clauses),
    {
      source_parameter: source_identity,
      target_parameter: target_identity,
      **edge_parameters,
    },
    "",
    "true",
  )


INSERT_DIRECTIVE = DirectiveMetadata(
  "insert",
  "directive @insert(key: GQL!, set: GQL!) on FIELD_DEFINITION",
  _attach_insert,
  _compile_entity_mutation,
  frozenset((OperationType.MUTATION,)),
)

UPDATE_DIRECTIVE = DirectiveMetadata(
  "update",
  "directive @update(key: GQL!, where: GQL, set: GQL!) on FIELD_DEFINITION",
  _attach_update,
  _compile_entity_mutation,
  frozenset((OperationType.MUTATION,)),
)

UPSERT_DIRECTIVE = DirectiveMetadata(
  "upsert",
  "directive @upsert(key: GQL!, insert: GQL, set: GQL) on FIELD_DEFINITION",
  _attach_upsert,
  _compile_entity_mutation,
  frozenset((OperationType.MUTATION,)),
)

DELETE_DIRECTIVE = DirectiveMetadata(
  "delete",
  "directive @delete(type: String!, key: GQL!) on FIELD_DEFINITION",
  _attach_delete,
  _compile_delete,
  frozenset((OperationType.MUTATION,)),
)

_RELATIONSHIP_DEFINITION = (
  "(fromType: String!, fromKey: GQL!, toType: String!, "
  "toKey: GQL!, field: String!, edge: GQL) on FIELD_DEFINITION"
)

CONNECT_DIRECTIVE = DirectiveMetadata(
  "connect",
  f"directive @connect{_RELATIONSHIP_DEFINITION}",
  _attach_connect,
  _compile_relationship,
  frozenset((OperationType.MUTATION,)),
)

DISCONNECT_DIRECTIVE = DirectiveMetadata(
  "disconnect",
  f"directive @disconnect{_RELATIONSHIP_DEFINITION}",
  _attach_disconnect,
  _compile_relationship,
  frozenset((OperationType.MUTATION,)),
)

MUTATION_DIRECTIVES = (
  INSERT_DIRECTIVE,
  UPDATE_DIRECTIVE,
  UPSERT_DIRECTIVE,
  DELETE_DIRECTIVE,
  CONNECT_DIRECTIVE,
  DISCONNECT_DIRECTIVE,
)
