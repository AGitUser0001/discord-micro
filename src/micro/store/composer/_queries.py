from dataclasses import dataclass

from graphql import Node, OperationType, StringValueNode

from ._composer import (
  Entity,
  GraphCompositionError,
  KeyBinding,
  _compile_key,
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
  key: KeyBinding
  owner: Entity
  owner_key: KeyBinding
  owner_field: str
  active_field: str


def _argument(context: DirectiveBindContext, name: str) -> Node:
  directive = next(
    item for item in context.field.directives or () if item.name.value == "fromActive"
  )
  argument = next(
    (item for item in directive.arguments or () if item.name.value == name), None
  )
  if argument is None:
    raise GraphCompositionError(f"@fromActive requires {name}.")
  return argument.value


def _attach(context: DirectiveBindContext) -> ActiveOwnedLookup:
  if (
    context.operation is not OperationType.QUERY
    or not isinstance(context.entity, Entity)
    or _is_list_type(context.field.type)
  ):
    raise GraphCompositionError("@fromActive must query one @entity.")
  owner_name_value = _argument(context, "ownerType")
  if not isinstance(owner_name_value, StringValueNode):
    raise GraphCompositionError("@fromActive ownerType must be a string.")
  owner_name = owner_name_value.value
  owner = context.entities.get(owner_name)
  if not isinstance(owner, Entity):
    raise GraphCompositionError("@fromActive ownerType must name an @entity.")
  owner_field_value = _argument(context, "ownerField")
  active_field_value = _argument(context, "activeField")
  if not isinstance(owner_field_value, StringValueNode) or not isinstance(
    active_field_value, StringValueNode
  ):
    raise GraphCompositionError("@fromActive field names must be strings.")
  owner_field = owner_field_value.value
  active_field = active_field_value.value
  if owner_field not in owner.fields or active_field not in owner.fields:
    raise GraphCompositionError("@fromActive references an unknown owner field.")
  arguments = {argument.name.value for argument in context.field.arguments or ()}
  key = _compile_key(_argument(context, "key"), arguments, "fromActive")
  owner_key = _compile_key(_argument(context, "ownerKey"), arguments, "fromActive")
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
    "directive @fromActive(key: GQL!, ownerType: String!, ownerKey: GQL!, "
    "ownerField: String!, activeField: String!) on FIELD_DEFINITION"
  ),
  _attach,
  _compile,
  frozenset((OperationType.QUERY,)),
)

MAX_PAGE_SIZE = 1000


@dataclass(frozen=True, slots=True)
class EntityScan:
  entity: Entity


def _attach_scan(context: DirectiveBindContext) -> EntityScan:
  if context.operation is not OperationType.QUERY or not isinstance(
    context.entity, Entity
  ):
    raise GraphCompositionError("@scan must return a list of an @entity type.")
  if not _is_list_type(context.field.type):
    raise GraphCompositionError("@scan must return a list.")
  arguments = {argument.name.value for argument in context.field.arguments or ()}
  if arguments != {"first", "offset"}:
    raise GraphCompositionError(
      "@scan fields must declare exactly first: Int! and offset: Int! arguments."
    )
  return EntityScan(context.entity)


def _compile_scan(context: DirectiveCompileContext) -> DirectiveResult:
  from .._compiler import physical_type

  binding = context.binding
  if not isinstance(binding, EntityScan):
    raise TypeError("@scan received invalid attached metadata.")
  first = context.arguments.get("first")
  offset = context.arguments.get("offset")
  if (
    not isinstance(first, int)
    or isinstance(first, bool)
    or not 1 <= first <= MAX_PAGE_SIZE
  ):
    raise ValueError(f"first must be between 1 and {MAX_PAGE_SIZE}.")
  if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0:
    raise ValueError("offset must be a non-negative integer.")
  first_parameter = f"{context.parameter_prefix}_first"
  offset_parameter = f"{context.parameter_prefix}_offset"
  return DirectiveResult(
    (f"MATCH ({context.variable}:{physical_type(binding.entity.name)})",),
    {first_parameter: first, offset_parameter: offset},
    binding.entity.name,
    tail=(
      f"ORDER BY {context.variable}._micro_id",
      f"SKIP ${offset_parameter}",
      f"LIMIT ${first_parameter}",
    ),
  )


SCAN_DIRECTIVE = DirectiveMetadata(
  "scan",
  "directive @scan on FIELD_DEFINITION",
  _attach_scan,
  _compile_scan,
  frozenset((OperationType.QUERY,)),
)

__all__ = (
  "FROM_ACTIVE_DIRECTIVE",
  "MAX_PAGE_SIZE",
  "SCAN_DIRECTIVE",
  "ActiveOwnedLookup",
  "EntityScan",
)
