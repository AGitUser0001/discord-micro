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
  NamedTypeNode,
  Node,
  NonNullTypeNode,
  StringValueNode,
  TypeNode,
)

from micro._store_module import StoreModule

_FEDERATION_SDL = """
  scalar federation__FieldSet

  directive @key(
    fields: federation__FieldSet!
    resolvable: Boolean = true
  ) repeatable on OBJECT | INTERFACE

  directive @resolve(key: String!) on FIELD_DEFINITION
"""


class FederationCompositionError(ValueError):
  pass


@dataclass(frozen=True, slots=True)
class ResolveExpression:
  source: str
  code: CodeType
  key_fields: tuple[str, ...]

  def evaluate(self, arguments: Mapping[str, object]) -> dict[str, object]:
    value = eval(self.code, {}, dict(arguments))
    if not isinstance(value, dict):
      raise TypeError("A @resolve key expression must produce a dict.")
    if set(value) != set(self.key_fields):
      raise ValueError("A @resolve key expression produced unexpected key fields.")
    return value


@dataclass(frozen=True, slots=True)
class Entity:
  name: str
  keys: tuple[tuple[str, ...], ...]


@dataclass(frozen=True, slots=True)
class RootResolver:
  operation: OperationType
  field: str
  entity: Entity
  expression: ResolveExpression


@dataclass(frozen=True, slots=True)
class FederatedGraph:
  schema: GraphQLSchema
  entities: Mapping[str, Entity]
  resolvers: Mapping[tuple[OperationType, str], RootResolver]
  modules: tuple[str, ...]


def compose_federation(modules: Sequence[StoreModule]) -> FederatedGraph:
  if not modules:
    raise FederationCompositionError("A federated graph needs at least one module.")
  module_ids = tuple(module.id for module in modules)
  if len(set(module_ids)) != len(module_ids):
    raise FederationCompositionError("Federation module IDs must be unique.")

  documents = tuple(parse(module.graphql_schema) for module in modules)
  schema_document = _merge_documents(documents)
  try:
    schema = build_ast_schema(schema_document)
  except Exception as exc:
    raise FederationCompositionError(str(exc)) from exc

  entities = _collect_entities(schema_document)
  resolvers = _collect_resolvers(schema_document, schema, entities)
  return FederatedGraph(
    schema,
    MappingProxyType(entities),
    MappingProxyType(resolvers),
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
        # Federation @link schema extensions do not affect the executable API schema.
        continue
      key = (definition.kind, name_node.value)
      previous = other_definitions.get(key)
      if previous is not None and print_ast(previous) != print_ast(definition):
        raise FederationCompositionError(
          f"Federation modules define incompatible {name_node.value!r} definitions."
        )
      other_definitions[key] = definition

  merged: list[Node] = list(parse(_FEDERATION_SDL).definitions)
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
          raise FederationCompositionError(
            f"Federation modules define incompatible field {name}.{field.name.value}."
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
      if directive.name.value != "key":
        continue
      fields_argument = next(
        (
          argument
          for argument in directive.arguments or ()
          if argument.name.value == "fields"
        ),
        None,
      )
      if fields_argument is None or not isinstance(
        fields_argument.value, StringValueNode
      ):
        raise FederationCompositionError(
          f"Entity {definition.name.value} has an invalid @key directive."
        )
      keys.append(_parse_flat_field_set(fields_argument.value.value))
    if keys:
      declared_fields = {field.name.value for field in definition.fields or ()}
      missing = {
        field_name
        for key in keys
        for field_name in key
        if field_name not in declared_fields
      }
      if missing:
        raise FederationCompositionError(
          f"Entity {definition.name.value} has @key fields which it does not "
          f"define: {', '.join(sorted(missing))}."
        )
      entities[definition.name.value] = Entity(definition.name.value, tuple(keys))
  return entities


def _collect_resolvers(
  document: DocumentNode,
  schema: GraphQLSchema,
  entities: Mapping[str, Entity],
) -> dict[tuple[OperationType, str], RootResolver]:
  root_names = {
    schema.query_type.name if schema.query_type else "": OperationType.QUERY,
    schema.mutation_type.name if schema.mutation_type else "": OperationType.MUTATION,
    schema.subscription_type.name
    if schema.subscription_type
    else "": OperationType.SUBSCRIPTION,
  }
  resolvers: dict[tuple[OperationType, str], RootResolver] = {}
  for definition in document.definitions:
    if not isinstance(definition, ObjectTypeDefinitionNode):
      continue
    operation = root_names.get(definition.name.value)
    if operation is None:
      continue
    for field in definition.fields or ():
      named_return = _named_type(field.type)
      entity = entities.get(named_return)
      directive = next(
        (item for item in field.directives or () if item.name.value == "resolve"),
        None,
      )
      if entity is not None and directive is None:
        raise FederationCompositionError(
          f"{definition.name.value}.{field.name.value} returns entity {entity.name} "
          "but does not declare @resolve."
        )
      if directive is None:
        continue
      if operation is not OperationType.QUERY:
        raise FederationCompositionError(
          "@resolve currently supports Query fields only; mutation semantics must "
          "be declared separately."
        )
      if entity is None:
        raise FederationCompositionError(
          f"{definition.name.value}.{field.name.value} declares @resolve but does "
          "not return a Federation entity."
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
        raise FederationCompositionError("@resolve requires a key expression.")
      argument_names = {argument.name.value for argument in field.arguments or ()}
      if _is_list_type(field.type):
        raise FederationCompositionError(
          f"{definition.name.value}.{field.name.value} uses @resolve but returns a list."
        )
      expression = _compile_resolve_expression(
        key_argument.value.value,
        argument_names,
      )
      if expression.key_fields not in entity.keys:
        raise FederationCompositionError(
          f"The @resolve key on {definition.name.value}.{field.name.value} does "
          f"not match a @key on {entity.name}."
        )
      resolvers[(operation, field.name.value)] = RootResolver(
        operation,
        field.name.value,
        entity,
        expression,
      )
  return resolvers


def _compile_resolve_expression(
  source: str,
  arguments: set[str],
) -> ResolveExpression:
  try:
    expression = ast.parse(source, mode="eval")
  except SyntaxError as exc:
    raise FederationCompositionError(
      f"Invalid @resolve Python expression: {exc}"
    ) from exc
  if not isinstance(expression.body, ast.Dict):
    raise FederationCompositionError("A @resolve expression must be a dict literal.")
  key_fields: list[str] = []
  for key in expression.body.keys:
    if not isinstance(key, ast.Constant) or not isinstance(key.value, str):
      raise FederationCompositionError("@resolve dict keys must be string literals.")
    key_fields.append(key.value)
  referenced_names = {
    node.id for node in ast.walk(expression) if isinstance(node, ast.Name)
  }
  unknown = referenced_names - arguments
  if unknown:
    raise FederationCompositionError(
      f"@resolve references unknown arguments: {', '.join(sorted(unknown))}."
    )
  return ResolveExpression(
    source,
    compile(expression, "<micro @resolve>", "eval"),
    tuple(key_fields),
  )


def _parse_flat_field_set(source: str) -> tuple[str, ...]:
  selection = parse(f"{{ {source} }}").definitions[0]
  selection_set = getattr(selection, "selection_set", None)
  if selection_set is None:
    raise FederationCompositionError("Invalid Federation field set.")
  fields: list[str] = []
  for item in selection_set.selections:
    if not hasattr(item, "name") or getattr(item, "selection_set", None) is not None:
      raise FederationCompositionError(
        "Nested Federation @key field sets are not supported yet."
      )
    fields.append(item.name.value)
  if not fields:
    raise FederationCompositionError("A Federation @key cannot be empty.")
  return tuple(fields)


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
