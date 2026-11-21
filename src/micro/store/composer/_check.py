"""`@check`: a field that runs GQL over the field's arguments and fails the request when
it finds something (`none:`) or nothing (`some:`). Put it before the writes it guards in
the same request: fields run in order in one transaction. The GQL uses the schema's names;
this compiles it to the physical ones."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal, cast

from graphglot import ast
from graphglot.dialect import Dialect
from graphql import NamedTypeNode, OperationType, StringValueNode
from pydantic import JsonValue

from ._composer import Entity, GraphCompositionError
from ._directive import (
  DirectiveBindContext,
  DirectiveCheck,
  DirectiveCompileContext,
  DirectiveMetadata,
  DirectiveResult,
)

_GQL = Dialect.get_or_raise("fullgql")


@dataclass(frozen=True, slots=True)
class CheckBinding:
  """A compiled `@check`: `statement` reads the field's `arguments` as parameters."""

  statement: str
  arguments: tuple[str, ...]
  fails_when: Literal["rows", "empty"]
  code: str
  message: str


def _attach_check(context: DirectiveBindContext) -> CheckBinding:
  where = f"@check on {context.field.name.value}"
  if context.return_type != "Boolean" or not isinstance(
    context.field.type, NamedTypeNode
  ):
    raise GraphCompositionError(
      f"{where}: the field returns Boolean (true when it passes)."
    )
  directive = next(
    item for item in context.field.directives or () if item.name.value == "check"
  )
  values = {
    argument.name.value: argument.value.value
    for argument in directive.arguments or ()
    if isinstance(argument.value, StringValueNode)
  }
  modes = [mode for mode in ("none", "some") if mode in values]
  if len(modes) != 1:
    raise GraphCompositionError(f"{where}: takes exactly one of none: or some:.")
  arguments = {argument.name.value for argument in context.field.arguments or ()}
  statement, used = compile_check(where, values[modes[0]], context.entities, arguments)
  return CheckBinding(
    statement,
    used,
    "rows" if modes[0] == "none" else "empty",
    values.get("code", "CONFLICT"),
    values["message"],
  )


def _compile_check(context: DirectiveCompileContext) -> DirectiveResult:
  binding = context.binding
  if not isinstance(binding, CheckBinding):
    raise TypeError("@check received invalid attached metadata.")
  return DirectiveResult(
    (),
    {},
    "",
    "true",
    checks=(
      DirectiveCheck(
        binding.statement,
        {
          name: cast(JsonValue, context.arguments.get(name))
          for name in binding.arguments
        },
        binding.fails_when,
        binding.code,
        binding.message,
      ),
    ),
  )


CHECK_DIRECTIVE = DirectiveMetadata(
  "check",
  'directive @check(none: String, some: String, code: String = "CONFLICT", '
  "message: String!) on FIELD_DEFINITION",
  _attach_check,
  _compile_check,
  frozenset((OperationType.MUTATION, OperationType.QUERY)),
)


def compile_check(
  where: str, source: str, entities: Mapping[str, Entity], arguments: set[str]
) -> tuple[str, tuple[str, ...]]:
  """The checking statement (`source`, then `RETURN 1 AS found`, with labels and
  properties made physical) and the field arguments it reads."""
  from .._compiler import physical_field, physical_reference, physical_type

  if "_micro_id" in source:
    raise GraphCompositionError(f"{where}: refer to fields by name.")
  try:
    tree = _GQL.parse(f"{source} RETURN 1 AS found")[0]
  except Exception as exc:
    raise GraphCompositionError(f"{where}: invalid GQL: {exc}") from exc

  types: dict[str, str | None] = {}
  """Each variable's entity type; None for an edge variable."""

  def variable(filler: Any) -> str | None:
    declared = filler.element_variable_declaration
    return None if declared is None else declared.element_variable.name

  def label(filler: Any) -> Any:
    expression = filler.is_label_expression
    if expression is None:
      return None
    names = [node for node in expression.dfs() if isinstance(node, ast.LabelName)]
    if len(names) != 1:
      raise GraphCompositionError(f"{where}: a pattern element takes one label.")
    return names[0].identifier

  for node in tree.dfs():  # node types first: edges and properties need them
    if isinstance(node, ast.NodePattern):
      filler = node.element_pattern_filler
      name, labelled = variable(filler), label(filler)
      if labelled is not None:
        if labelled.name not in entities:
          raise GraphCompositionError(
            f"{where}: {labelled.name} is not an @entity type."
          )
        if name is not None:
          types[name] = labelled.name

  def node_type(element: Any) -> str:
    filler = element.element_pattern_filler
    labelled = label(filler)
    if labelled is not None:
      return labelled.name
    name = variable(filler)
    known = types.get(name) if name is not None else None
    if known is None:
      raise GraphCompositionError(f"{where}: give each end of an edge a type.")
    return known

  renames: list[tuple[Any, str]] = []
  for path in [node for node in tree.dfs() if isinstance(node, ast.PathPattern)]:
    elements = [
      node
      for node in path.dfs()
      if isinstance(node, ast.NodePattern) or type(node).__name__.startswith("FullEdge")
    ]
    for index, element in enumerate(elements):
      if isinstance(element, ast.NodePattern):
        labelled = label(element.element_pattern_filler)
        if labelled is not None:
          renames.append((labelled, physical_type(labelled.name)))
        continue
      kind = type(element).__name__
      if kind not in ("FullEdgePointingRight", "FullEdgePointingLeft"):
        raise GraphCompositionError(f"{where}: an edge needs a direction (-> or <-).")
      start = elements[index - 1 if kind == "FullEdgePointingRight" else index + 1]
      source_type = node_type(start)
      filler: Any = getattr(element, "element_pattern_filler")  # noqa: B009  # FullEdge*
      name, field = variable(filler), label(filler)
      if name is not None:
        types[name] = None
      if field is None:
        raise GraphCompositionError(
          f"{where}: name an edge by its field (-[:field]->)."
        )
      if field.name not in entities[source_type].fields:
        raise GraphCompositionError(
          f"{where}: {source_type} has no field {field.name}."
        )
      renames.append((field, physical_reference(f"{source_type}.{field.name}")))

  parameters: list[str] = []
  for node in tree.dfs():
    if isinstance(node, ast.GeneralParameterReference):
      name = node.parameter_name.name
      if name not in arguments:
        raise GraphCompositionError(
          f"{where}: ${name} is not an argument of the field."
        )
      if name not in parameters:
        parameters.append(name)
      continue
    if not isinstance(node, ast.PropertyReference):
      continue
    owner = node.property_source
    if not isinstance(owner, ast.BindingVariableReference):
      raise GraphCompositionError(f"{where}: properties belong to a pattern variable.")
    field = node.property_name[0].identifier
    if owner.binding_variable.name not in types:
      raise GraphCompositionError(
        f"{where}: {owner.binding_variable.name} is not a variable of the pattern."
      )
    owner_type = types[owner.binding_variable.name]
    if owner_type is None:
      continue  # an edge's own properties keep their names
    if field.name not in entities[owner_type].fields:
      raise GraphCompositionError(f"{where}: {owner_type} has no field {field.name}.")
    renames.append((field, physical_field(f"{owner_type}.{field.name}")))

  for identifier, physical in renames:
    identifier.name = physical
  rendered = _GQL.generate(tree)
  validation = _GQL.validate(rendered)
  if not validation.success:
    problems = "; ".join(str(item) for item in validation.diagnostics)
    raise GraphCompositionError(f"{where}: {problems}")
  return rendered, tuple(parameters)


__all__ = ("CHECK_DIRECTIVE", "CheckBinding", "compile_check")
