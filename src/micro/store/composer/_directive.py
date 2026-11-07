from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from graphql import FieldDefinitionNode, ObjectTypeDefinitionNode, OperationType
from pydantic import JsonValue


@dataclass(frozen=True, slots=True)
class DirectiveBindContext:
  """What a directive's `bind` receives: the field, entities and arguments."""

  operation: OperationType | None
  parent_type: str
  field: FieldDefinitionNode
  return_type: str
  entity: Any | None
  entities: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class DirectiveCompileContext:
  """What a directive's `compile` receives while an operation is compiled."""

  operation: OperationType
  field: str
  return_type: str
  arguments: Mapping[str, object]
  variable: str
  parent_variable: str | None
  parameter_prefix: str
  binding: Any


@dataclass(frozen=True, slots=True)
class DirectiveResult:
  """What a directive's `compile` returns: statements and how to shape the result."""

  clauses: tuple[str, ...]
  parameters: Mapping[str, JsonValue]
  path: str
  value: str | None = None
  tail: tuple[str, ...] = ()


type DirectiveBinder = Callable[[DirectiveBindContext], Any]
type DirectiveCompiler = Callable[[DirectiveCompileContext], DirectiveResult]


@dataclass(frozen=True, slots=True)
class DirectiveMetadata:
  """Schema definition and Python behavior for a root-field directive."""

  name: str
  definition: str
  bind: DirectiveBinder
  compile: DirectiveCompiler
  operations: frozenset[OperationType] = frozenset(OperationType)


@dataclass(frozen=True, slots=True)
class DirectiveBinding:
  """What a directive's `bind` returns: how to execute the field."""

  directive: DirectiveMetadata
  value: Any
  return_type: str


@dataclass(frozen=True, slots=True)
class TypeDirectiveBindContext:
  """What a type directive's attach function receives."""

  type: ObjectTypeDefinitionNode


type TypeDirectiveAttacher = Callable[[TypeDirectiveBindContext], Any]


@dataclass(frozen=True, slots=True)
class TypeDirectiveMetadata:
  """A type directive: name, SDL definition and attach function."""

  name: str
  definition: str
  attach: TypeDirectiveAttacher


@dataclass(frozen=True, slots=True)
class TypeDirectiveBinding:
  """What a type directive's attach function returns."""

  directive: TypeDirectiveMetadata
  value: Any
