from dataclasses import dataclass

from graphql import OperationType, StringValueNode

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
class ActiveOwnedLookup:
  entity: Entity
  key: FromExpression
  owner: Entity
  owner_key: FromExpression
  owner_field: str
  active_field: str


def _argument(context: DirectiveBindContext, name: str) -> str:
  directive = next(
    item for item in context.field.directives or () if item.name.value == "fromActive"
  )
  argument = next(
    (item for item in directive.arguments or () if item.name.value == name), None
  )
  if argument is None or not isinstance(argument.value, StringValueNode):
    raise GraphCompositionError(f"@fromActive requires {name}: String!.")
  return argument.value.value


def _attach(context: DirectiveBindContext) -> ActiveOwnedLookup:
  if (
    context.operation is not OperationType.QUERY
    or not isinstance(context.entity, Entity)
    or _is_list_type(context.field.type)
  ):
    raise GraphCompositionError("@fromActive must query one @entity.")
  owner_name = _argument(context, "ownerType")
  owner = context.entities.get(owner_name)
  if not isinstance(owner, Entity):
    raise GraphCompositionError("@fromActive ownerType must name an @entity.")
  owner_field = _argument(context, "ownerField")
  active_field = _argument(context, "activeField")
  if owner_field not in owner.fields or active_field not in owner.fields:
    raise GraphCompositionError("@fromActive references an unknown owner field.")
  arguments = {argument.name.value for argument in context.field.arguments or ()}
  key = _compile_from_expression(_argument(context, "key"), arguments)
  owner_key = _compile_from_expression(_argument(context, "ownerKey"), arguments)
  if (
    key.key_fields not in context.entity.keys or owner_key.key_fields not in owner.keys
  ):
    raise GraphCompositionError("@fromActive key does not match an @entity key.")
  return ActiveOwnedLookup(
    context.entity, key, owner, owner_key, owner_field, active_field
  )


def _compile(context: DirectiveCompileContext) -> DirectiveResult:
  from .._compiler import (
    entity_identity,
    physical_field,
    physical_reference,
    physical_type,
  )

  binding = context.binding
  if not isinstance(binding, ActiveOwnedLookup):
    raise TypeError("@fromActive received invalid attached metadata.")
  owner_variable = f"{context.variable}_owner"
  key_parameter = f"{context.parameter_prefix}_identity"
  owner_parameter = f"{context.parameter_prefix}_owner"
  return DirectiveResult(
    (
      (
        f"OPTIONAL MATCH ({owner_variable}:{physical_type(binding.owner.name)})-"
        f"[:{physical_reference(f'{binding.owner.name}.{binding.owner_field}')}]->"
        f"({context.variable}:{physical_type(binding.entity.name)})"
      ),
      (
        f"WHERE {owner_variable}._micro_id = ${owner_parameter} AND "
        f"{context.variable}._micro_id = ${key_parameter} AND "
        f"{owner_variable}."
        f"{physical_field(f'{binding.owner.name}.{binding.active_field}')} = true"
      ),
    ),
    {
      key_parameter: entity_identity(
        binding.entity.name, binding.key.evaluate(context.arguments)
      ),
      owner_parameter: entity_identity(
        binding.owner.name, binding.owner_key.evaluate(context.arguments)
      ),
    },
    binding.entity.name,
  )


FROM_ACTIVE_DIRECTIVE = DirectiveMetadata(
  "fromActive",
  (
    "directive @fromActive(key: String!, ownerType: String!, ownerKey: String!, "
    "ownerField: String!, activeField: String!) on FIELD_DEFINITION"
  ),
  _attach,
  _compile,
  frozenset((OperationType.QUERY,)),
)

__all__ = ("FROM_ACTIVE_DIRECTIVE", "ActiveOwnedLookup")
