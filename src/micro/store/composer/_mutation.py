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
)

_GQL = Dialect.get_or_raise("fullgql")


@dataclass(frozen=True, slots=True)
class GQLExpression:
  tree: Any
  parameters: frozenset[str]

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


def compile_gql_expression(
  source: str, entity: Entity, arguments: set[str]
) -> GQLExpression:
  try:
    tree = _GQL.parse(f"RETURN {source}")[0]
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
  return GQLExpression(tree, frozenset(parameters))


@dataclass(frozen=True, slots=True)
class Assignment:
  field: str
  argument: str | None = None
  expression: GQLExpression | None = None


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
  key: KeyBinding
  assignments: tuple[Assignment, ...]
  where: GQLExpression | None


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


def _directive_argument(context: DirectiveBindContext, name: str):
  directive = next(
    item
    for item in context.field.directives or ()
    if item.name.value in {"insert", "update", "delete", "connect", "disconnect"}
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


def _attach_entity_mutation(
  context: DirectiveBindContext,
  action: Literal["insert", "update"],
) -> EntityMutation:
  _require_mutation(context, action)
  if not isinstance(context.entity, Entity):
    raise GraphCompositionError(f"@{action} must return an @entity type.")
  arguments = _mutation_arguments(context)
  key = _compile_key(_directive_argument(context, "key"), arguments, action)
  set_value = _directive_argument(context, "set")
  if not isinstance(set_value, ObjectValueNode) or not set_value.fields:
    raise GraphCompositionError(f"@{action} set must be a non-empty object.")
  assignments: list[Assignment] = []
  for field in set_value.fields:
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
          expression=compile_gql_expression(
            field.value.value, context.entity, arguments
          ),
        )
      )
    else:
      raise GraphCompositionError(
        f"@{action} set values must be argument names or GQL strings."
      )
  if key.key_fields not in context.entity.keys:
    raise GraphCompositionError(f"@{action} key does not match an @entity key.")
  unknown = {assignment.field for assignment in assignments} - context.entity.fields
  if unknown:
    raise GraphCompositionError(
      f"@{action} references unknown fields: {', '.join(sorted(unknown))}."
    )
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
  identity_parameter = f"{context.parameter_prefix}_identity"
  parameters: dict[str, JsonValue] = {
    identity_parameter: entity_identity(binding.entity.name, key)
  }
  properties: list[str] = [f"_micro_id: ${identity_parameter}"]
  assignments: list[str] = []
  for assignment in binding.assignments:
    physical = physical_field(f"{binding.entity.name}.{assignment.field}")
    if assignment.argument is not None:
      if assignment.argument not in context.arguments:
        continue  # not passed: an insert leaves it unset, an update leaves it as it is
      parameter = f"{context.parameter_prefix}_{assignment.argument}"
      parameters[parameter] = cast(JsonValue, context.arguments[assignment.argument])
      value = f"${parameter}"
    else:
      assert assignment.expression is not None
      value, expression_parameters = assignment.expression.render(
        binding.entity,
        context.variable,
        context.parameter_prefix,
        dict(context.arguments),
      )
      parameters.update(expression_parameters)
    properties.append(f"{physical}: {value}")
    assignments.append(f"{context.variable}.{physical} = {value}")
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
  return DirectiveResult(clauses, parameters, binding.entity.name)


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

DELETE_DIRECTIVE = DirectiveMetadata(
  "delete",
  "directive @delete(type: String!, key: GQL!) on FIELD_DEFINITION",
  _attach_delete,
  _compile_delete,
  frozenset((OperationType.MUTATION,)),
)

_RELATIONSHIP_DEFINITION = (
  "(fromType: String!, fromKey: GQL!, toType: String!, "
  "toKey: GQL!, field: String!) on FIELD_DEFINITION"
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
