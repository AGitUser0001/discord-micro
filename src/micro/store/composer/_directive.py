from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from graphql import FieldDefinitionNode, ObjectTypeDefinitionNode, OperationType
from pydantic import JsonValue


@dataclass(frozen=True, slots=True)
class DirectiveBindContext:
  operation: OperationType | None
  parent_type: str
  field: FieldDefinitionNode
  return_type: str
  entity: Any | None


@dataclass(frozen=True, slots=True)
class DirectiveCompileContext:
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
  clauses: tuple[str, ...]
  parameters: Mapping[str, JsonValue]
  path: str
  value: str | None = None


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
  directive: DirectiveMetadata
  value: Any
  return_type: str


@dataclass(frozen=True, slots=True)
class TypeDirectiveBindContext:
  type: ObjectTypeDefinitionNode


type TypeDirectiveAttacher = Callable[[TypeDirectiveBindContext], Any]


@dataclass(frozen=True, slots=True)
class TypeDirectiveMetadata:
  name: str
  definition: str
  attach: TypeDirectiveAttacher


@dataclass(frozen=True, slots=True)
class TypeDirectiveBinding:
  directive: TypeDirectiveMetadata
  value: Any
