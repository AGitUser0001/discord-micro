from dataclasses import dataclass
from typing import Literal, cast

from graphql import OperationType, StringValueNode
from pydantic import JsonValue

from ._composer import (
  Entity,
  FromExpression,
  GraphCompositionError,
  _compile_from_expression,
  _is_list_type,
)
from ._directive import (
  DirectiveBindContext,
  DirectiveCompileContext,
  DirectiveMetadata,
  DirectiveResult,
)


@dataclass(frozen=True, slots=True)
class EntityMutation:
  action: Literal["insert", "update"]
  entity: Entity
  key: FromExpression
  fields: FromExpression


@dataclass(frozen=True, slots=True)
class DeleteMutation:
  entity: Entity
  key: FromExpression


@dataclass(frozen=True, slots=True)
class RelationshipMutation:
  action: Literal["connect", "disconnect"]
  source: Entity
  source_key: FromExpression
  target: Entity
  target_key: FromExpression
  field: str


def _directive_argument(context: DirectiveBindContext, name: str) -> str:
  directive = next(
    item
    for item in context.field.directives or ()
    if item.name.value in {"insert", "update", "delete", "connect", "disconnect"}
  )
  argument = next(
    (item for item in directive.arguments or () if item.name.value == name),
    None,
  )
  if argument is None or not isinstance(argument.value, StringValueNode):
    raise GraphCompositionError(f"@{directive.name.value} requires {name}: String!.")
  return argument.value.value


def _mutation_arguments(context: DirectiveBindContext) -> set[str]:
  return {argument.name.value for argument in context.field.arguments or ()}


def _require_mutation(context: DirectiveBindContext, name: str) -> None:
  if context.operation is not OperationType.MUTATION:
    raise GraphCompositionError(f"@{name} supports Mutation fields only.")
  if _is_list_type(context.field.type):
    raise GraphCompositionError(f"@{name} does not support list return types.")


def _attach_entity_mutation(
  context: DirectiveBindContext,
  action: Literal["insert", "update"],
) -> EntityMutation:
  _require_mutation(context, action)
  if not isinstance(context.entity, Entity):
    raise GraphCompositionError(f"@{action} must return an @entity type.")
  arguments = _mutation_arguments(context)
  key = _compile_from_expression(_directive_argument(context, "key"), arguments)
  fields = _compile_from_expression(_directive_argument(context, "fields"), arguments)
  if key.key_fields not in context.entity.keys:
    raise GraphCompositionError(f"@{action} key does not match an @entity key.")
  unknown = set(fields.key_fields) - context.entity.fields
  if unknown:
    raise GraphCompositionError(
      f"@{action} references unknown fields: {', '.join(sorted(unknown))}."
    )
  if not fields.key_fields:
    raise GraphCompositionError(f"@{action} fields cannot be empty.")
  if action == "insert" and not set(key.key_fields) <= set(fields.key_fields):
    raise GraphCompositionError("@insert fields must include every entity key field.")
  return EntityMutation(action, context.entity, key, fields)


def _attach_insert(context: DirectiveBindContext) -> EntityMutation:
  return _attach_entity_mutation(context, "insert")


def _attach_update(context: DirectiveBindContext) -> EntityMutation:
  return _attach_entity_mutation(context, "update")


def _compile_entity_mutation(context: DirectiveCompileContext) -> DirectiveResult:
  from .._compiler import entity_identity, physical_field, physical_type

  binding = context.binding
  if not isinstance(binding, EntityMutation):
    raise TypeError("Entity mutation received invalid attached metadata.")
  key = binding.key.evaluate(context.arguments)
  fields = binding.fields.evaluate(context.arguments)
  identity_parameter = f"{context.parameter_prefix}_identity"
  parameters: dict[str, JsonValue] = {
    identity_parameter: entity_identity(binding.entity.name, key)
  }
  properties: list[str] = [f"_micro_id: ${identity_parameter}"]
  assignments: list[str] = []
  for field_name, value in fields.items():
    parameter = f"{context.parameter_prefix}_{field_name}"
    parameters[parameter] = cast(JsonValue, value)
    physical = physical_field(f"{binding.entity.name}.{field_name}")
    properties.append(f"{physical}: ${parameter}")
    assignments.append(f"{context.variable}.{physical} = ${parameter}")
  if binding.action == "insert":
    clauses = (
      (
        f"INSERT ({context.variable}:{physical_type(binding.entity.name)} "
        f"{{{', '.join(properties)}}})"
      ),
    )
  else:
    clauses = (
      f"MATCH ({context.variable}:{physical_type(binding.entity.name)})",
      f"WHERE {context.variable}._micro_id = ${identity_parameter}",
      f"SET {', '.join(assignments)}",
    )
  return DirectiveResult(clauses, parameters, binding.entity.name)


def _attach_delete(context: DirectiveBindContext) -> DeleteMutation:
  _require_mutation(context, "delete")
  entity_name = _directive_argument(context, "type")
  entity = context.entities.get(entity_name)
  if not isinstance(entity, Entity):
    raise GraphCompositionError(f"@delete references unknown entity {entity_name!r}.")
  key = _compile_from_expression(
    _directive_argument(context, "key"), _mutation_arguments(context)
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
  source_name = _directive_argument(context, "fromType")
  target_name = _directive_argument(context, "toType")
  source = context.entities.get(source_name)
  target = context.entities.get(target_name)
  if not isinstance(source, Entity) or not isinstance(target, Entity):
    raise GraphCompositionError(f"@{action} references an unknown entity type.")
  field = _directive_argument(context, "field")
  if field not in source.fields:
    raise GraphCompositionError(
      f"@{action} references unknown field {source.name}.{field}."
    )
  arguments = _mutation_arguments(context)
  source_key = _compile_from_expression(
    _directive_argument(context, "fromKey"), arguments
  )
  target_key = _compile_from_expression(
    _directive_argument(context, "toKey"), arguments
  )
  if (
    source_key.key_fields not in source.keys or target_key.key_fields not in target.keys
  ):
    raise GraphCompositionError(f"@{action} key does not match an @entity key.")
  return RelationshipMutation(action, source, source_key, target, target_key, field)


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
  if binding.action == "connect":
    clauses.append(
      f"INSERT ({source_variable})-[:{relationship_type}]->({target_variable})"
    )
  else:
    clauses[0] = (
      f"MATCH ({source_variable}:{physical_type(binding.source.name)})-"
      f"[{relationship_variable}:{relationship_type}]->"
      f"({target_variable}:{physical_type(binding.target.name)})"
    )
    clauses.append(f"DELETE {relationship_variable}")
  return DirectiveResult(
    tuple(clauses),
    {
      source_parameter: entity_identity(
        binding.source.name, binding.source_key.evaluate(context.arguments)
      ),
      target_parameter: entity_identity(
        binding.target.name, binding.target_key.evaluate(context.arguments)
      ),
    },
    "",
    "true",
  )


INSERT_DIRECTIVE = DirectiveMetadata(
  "insert",
  "directive @insert(key: String!, fields: String!) on FIELD_DEFINITION",
  _attach_insert,
  _compile_entity_mutation,
  frozenset((OperationType.MUTATION,)),
)

UPDATE_DIRECTIVE = DirectiveMetadata(
  "update",
  "directive @update(key: String!, fields: String!) on FIELD_DEFINITION",
  _attach_update,
  _compile_entity_mutation,
  frozenset((OperationType.MUTATION,)),
)

DELETE_DIRECTIVE = DirectiveMetadata(
  "delete",
  "directive @delete(type: String!, key: String!) on FIELD_DEFINITION",
  _attach_delete,
  _compile_delete,
  frozenset((OperationType.MUTATION,)),
)

_RELATIONSHIP_DEFINITION = (
  "(fromType: String!, fromKey: String!, toType: String!, "
  "toKey: String!, field: String!) on FIELD_DEFINITION"
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
  DELETE_DIRECTIVE,
  CONNECT_DIRECTIVE,
  DISCONNECT_DIRECTIVE,
)
