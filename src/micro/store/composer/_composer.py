import ast
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import CodeType, MappingProxyType

from graphql import (
  DocumentNode,
  FieldDefinitionNode,
  GraphQLSchema,
  ObjectTypeDefinitionNode,
  ObjectTypeExtensionNode,
  OperationType,
  build_ast_schema,
  parse,
  print_ast,
)
from graphql.language import (
  ListTypeNode,
  ListValueNode,
  NamedTypeNode,
  Node,
  NonNullTypeNode,
  StringValueNode,
  TypeNode,
)

from .._module import GraphModule

_MICRO_GRAPH_SDL = """
  directive @entity(key: [String!]!) repeatable on OBJECT
  directive @from(key: String!) on FIELD_DEFINITION
"""


class GraphCompositionError(ValueError):
  pass


@dataclass(frozen=True, slots=True)
class FromExpression:
  """A validated Python key expression evaluated for each root-field request."""

  source: str
  code: CodeType
  key_fields: tuple[str, ...]

  def evaluate(self, arguments: Mapping[str, object]) -> dict[str, object]:
    value = eval(self.code, {"__builtins__": {}}, dict(arguments))
    if not isinstance(value, dict):
      raise TypeError("A @from key expression must produce a dict.")
    if set(value) != set(self.key_fields):
      raise ValueError("A @from key expression produced unexpected key fields.")
    return value


@dataclass(frozen=True, slots=True)
class Entity:
  name: str
  keys: tuple[tuple[str, ...], ...]


@dataclass(frozen=True, slots=True)
class EntityLookup:
  operation: OperationType
  field: str
  entity: Entity
  expression: FromExpression


@dataclass(frozen=True, slots=True)
class MicroGraph:
  schema: GraphQLSchema
  entities: Mapping[str, Entity]
  lookups: Mapping[tuple[OperationType, str], EntityLookup]
  modules: tuple[str, ...]


def compose_graph(modules: Sequence[GraphModule]) -> MicroGraph:
  if not modules:
    raise GraphCompositionError("A graph needs at least one module.")
  module_ids = tuple(module.id for module in modules)
  if len(set(module_ids)) != len(module_ids):
    raise GraphCompositionError("Graph module IDs must be unique.")

  documents = tuple(parse(module.graphql_schema) for module in modules)
  schema_document = _merge_documents(documents)
  try:
    schema = build_ast_schema(schema_document)
  except Exception as exc:
    raise GraphCompositionError(str(exc)) from exc

  entities = _collect_entities(schema_document)
  lookups = _collect_lookups(schema_document, schema, entities)
  return MicroGraph(
    schema,
    MappingProxyType(entities),
    MappingProxyType(lookups),
    module_ids,
  )


def _merge_documents(documents: Sequence[DocumentNode]) -> DocumentNode:
  object_definitions: dict[
    str, list[ObjectTypeDefinitionNode | ObjectTypeExtensionNode]
  ] = defaultdict(list)
  other_definitions: dict[tuple[str, str], Node] = {}

  for document in documents:
    for definition in document.definitions:
      if isinstance(definition, ObjectTypeDefinitionNode | ObjectTypeExtensionNode):
        object_definitions[definition.name.value].append(definition)
        continue
      name_node = getattr(definition, "name", None)
      if name_node is None:
        continue
      key = (definition.kind, name_node.value)
      previous = other_definitions.get(key)
      if previous is not None and print_ast(previous) != print_ast(definition):
        raise GraphCompositionError(
          f"Graph modules define incompatible {name_node.value!r} definitions."
        )
      other_definitions[key] = definition

  merged: list[Node] = list(parse(_MICRO_GRAPH_SDL).definitions)
  merged.extend(other_definitions.values())
  for name, definitions in object_definitions.items():
    fields: dict[str, FieldDefinitionNode] = {}
    directives: dict[str, Node] = {}
    interfaces: dict[str, NamedTypeNode] = {}
    description = None
    for definition in definitions:
      description = description or getattr(definition, "description", None)
      for field in definition.fields or ():
        previous = fields.get(field.name.value)
        if previous is not None and print_ast(previous) != print_ast(field):
          raise GraphCompositionError(
            f"Graph modules define incompatible field {name}.{field.name.value}."
          )
        fields[field.name.value] = field
      for directive in definition.directives or ():
        directives[print_ast(directive)] = directive
      for interface in definition.interfaces or ():
        interfaces[interface.name.value] = interface
    merged.append(
      ObjectTypeDefinitionNode(
        name=definitions[0].name,
        description=description,
        fields=tuple(fields.values()),
        directives=tuple(directives.values()),
        interfaces=tuple(interfaces.values()),
      )
    )
  return DocumentNode(definitions=tuple(merged))


def _collect_entities(document: DocumentNode) -> dict[str, Entity]:
  entities: dict[str, Entity] = {}
  for definition in document.definitions:
    if not isinstance(definition, ObjectTypeDefinitionNode):
      continue
    keys: list[tuple[str, ...]] = []
    for directive in definition.directives or ():
      if directive.name.value != "entity":
        continue
      key_argument = next(
        (
          argument
          for argument in directive.arguments or ()
          if argument.name.value == "key"
        ),
        None,
      )
      if key_argument is None or not isinstance(key_argument.value, ListValueNode):
        raise GraphCompositionError(
          f"Entity {definition.name.value} has an invalid @entity directive."
        )
      key = tuple(
        value.value
        for value in key_argument.value.values
        if isinstance(value, StringValueNode)
      )
      if len(key) != len(key_argument.value.values) or not key:
        raise GraphCompositionError(
          f"Entity {definition.name.value} must declare a non-empty string key."
        )
      if len(set(key)) != len(key):
        raise GraphCompositionError(
          f"Entity {definition.name.value} declares duplicate key fields."
        )
      if key not in keys:
        keys.append(key)
    if keys:
      declared_fields = {field.name.value for field in definition.fields or ()}
      missing = {
        field_name
        for key in keys
        for field_name in key
        if field_name not in declared_fields
      }
      if missing:
        raise GraphCompositionError(
          f"Entity {definition.name.value} has key fields which it does not define: "
          f"{', '.join(sorted(missing))}."
        )
      entities[definition.name.value] = Entity(definition.name.value, tuple(keys))
  return entities


def _collect_lookups(
  document: DocumentNode,
  schema: GraphQLSchema,
  entities: Mapping[str, Entity],
) -> dict[tuple[OperationType, str], EntityLookup]:
  root_names = {
    schema.query_type.name if schema.query_type else "": OperationType.QUERY,
    schema.mutation_type.name if schema.mutation_type else "": OperationType.MUTATION,
    schema.subscription_type.name
    if schema.subscription_type
    else "": OperationType.SUBSCRIPTION,
  }
  lookups: dict[tuple[OperationType, str], EntityLookup] = {}
  for definition in document.definitions:
    if not isinstance(definition, ObjectTypeDefinitionNode):
      continue
    operation = root_names.get(definition.name.value)
    if operation is None:
      continue
    for field in definition.fields or ():
      entity = entities.get(_named_type(field.type))
      directive = next(
        (item for item in field.directives or () if item.name.value == "from"),
        None,
      )
      if entity is not None and directive is None:
        raise GraphCompositionError(
          f"{definition.name.value}.{field.name.value} returns entity {entity.name} "
          "but does not declare @from."
        )
      if directive is None:
        continue
      if operation is not OperationType.QUERY:
        raise GraphCompositionError(
          "@from currently supports Query fields only; mutation semantics must "
          "use a different runtime macro."
        )
      if entity is None:
        raise GraphCompositionError(
          f"{definition.name.value}.{field.name.value} declares @from but does "
          "not return an entity."
        )
      key_argument = next(
        (
          argument
          for argument in directive.arguments or ()
          if argument.name.value == "key"
        ),
        None,
      )
      if key_argument is None or not isinstance(key_argument.value, StringValueNode):
        raise GraphCompositionError("@from requires a key expression.")
      if _is_list_type(field.type):
        raise GraphCompositionError(
          f"{definition.name.value}.{field.name.value} uses @from but returns a list."
        )
      expression = _compile_from_expression(
        key_argument.value.value,
        {argument.name.value for argument in field.arguments or ()},
      )
      if expression.key_fields not in entity.keys:
        raise GraphCompositionError(
          f"The @from key on {definition.name.value}.{field.name.value} does "
          f"not match an @entity key on {entity.name}."
        )
      lookups[(operation, field.name.value)] = EntityLookup(
        operation,
        field.name.value,
        entity,
        expression,
      )
  return lookups


def _compile_from_expression(source: str, arguments: set[str]) -> FromExpression:
  try:
    expression = ast.parse(source, mode="eval")
  except SyntaxError as exc:
    raise GraphCompositionError(f"Invalid @from Python expression: {exc}") from exc
  if not isinstance(expression.body, ast.Dict):
    raise GraphCompositionError("A @from expression must be a dict literal.")
  key_fields: list[str] = []
  for key in expression.body.keys:
    if not isinstance(key, ast.Constant) or not isinstance(key.value, str):
      raise GraphCompositionError("@from dict keys must be string literals.")
    key_fields.append(key.value)
  if len(set(key_fields)) != len(key_fields):
    raise GraphCompositionError("@from cannot produce duplicate key fields.")
  referenced_names = {
    node.id for node in ast.walk(expression) if isinstance(node, ast.Name)
  }
  unknown = referenced_names - arguments
  if unknown:
    raise GraphCompositionError(
      f"@from references unknown arguments: {', '.join(sorted(unknown))}."
    )
  return FromExpression(
    source,
    compile(expression, "<micro @from>", "eval"),
    tuple(key_fields),
  )


def _named_type(type_node: TypeNode) -> str:
  current = type_node
  while not isinstance(current, NamedTypeNode):
    if not isinstance(current, ListTypeNode | NonNullTypeNode):
      raise TypeError("Unexpected GraphQL type node.")
    current = current.type
  return current.name.value


def _is_list_type(type_node: TypeNode) -> bool:
  current = type_node
  if isinstance(current, NonNullTypeNode):
    current = current.type
  return isinstance(current, ListTypeNode)
