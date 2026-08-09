from dataclasses import dataclass

from graphql import OperationType

from ._composer import Entity, GraphCompositionError, _is_list_type
from ._directive import (
  DirectiveBindContext,
  DirectiveCompileContext,
  DirectiveMetadata,
  DirectiveResult,
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


__all__ = ("MAX_PAGE_SIZE", "SCAN_DIRECTIVE", "EntityScan")
