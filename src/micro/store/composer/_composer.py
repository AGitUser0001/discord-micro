from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, cast

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
  EnumTypeDefinitionNode,
  EnumTypeExtensionNode,
  EnumValueNode,
  InputObjectTypeDefinitionNode,
  InputObjectTypeExtensionNode,
  InterfaceTypeDefinitionNode,
  InterfaceTypeExtensionNode,
  ListTypeNode,
  ListValueNode,
  NamedTypeNode,
  Node,
  NonNullTypeNode,
  ObjectValueNode,
  SchemaDefinitionNode,
  SchemaExtensionNode,
  StringValueNode,
  TypeNode,
  UnionTypeDefinitionNode,
  UnionTypeExtensionNode,
)

from micro.errors import TopologyError

from .._module import GraphModule
from ._directive import (
  DirectiveBindContext,
  DirectiveBinding,
  DirectiveCompileContext,
  DirectiveMetadata,
  DirectiveResult,
  TypeDirectiveBindContext,
  TypeDirectiveBinding,
  TypeDirectiveMetadata,
)


class GraphCompositionError(TopologyError):
  pass


@dataclass(frozen=True, slots=True)
class KeyBinding:
  """A declarative entity-field to GraphQL-argument mapping."""

  fields: tuple[tuple[str, str], ...]

  @property
  def key_fields(self) -> tuple[str, ...]:
    return tuple(field for field, _ in self.fields)

  def evaluate(self, arguments: Mapping[str, object]) -> dict[str, object]:
    return {field: arguments[argument] for field, argument in self.fields}


@dataclass(frozen=True, slots=True)
class FromDirective:
  """The binding of `@from`."""

  entity: Entity
  expression: KeyBinding


@dataclass(frozen=True, slots=True)
class Entity:
  """A stored type with its key fields."""

  name: str
  keys: tuple[tuple[str, ...], ...]
  fields: frozenset[str]
  maps: tuple[tuple[str, str, str], ...] = ()
  """`(field, key scalar, value scalar)` for each `Map @map(key: K, value: V)` field."""


@dataclass(frozen=True, slots=True)
class MicroGraph:
  """The GraphQL schema, compiler and executor of a store, together."""

  schema: GraphQLSchema
  entities: Mapping[str, Entity]
  bindings: Mapping[tuple[str, str], DirectiveBinding]
  modules: tuple[str, ...]
  directives: Mapping[str, DirectiveMetadata]
  type_bindings: Mapping[str, Mapping[str, TypeDirectiveBinding]]


def compose_graph(
  modules: Sequence[GraphModule],
  *,
  directives: Sequence[DirectiveMetadata] = (),
  type_directives: Sequence[TypeDirectiveMetadata] = (),
) -> MicroGraph:
  """Compose modules and directives into one validated GraphQL schema."""
  if not modules:
    raise GraphCompositionError("A graph needs at least one module.")
  module_ids = tuple(module.id for module in modules)
  if len(set(module_ids)) != len(module_ids):
    raise GraphCompositionError("Graph module IDs must be unique.")

  from ._mutation import MUTATION_DIRECTIVES
  from ._queries import FROM_ACTIVE_DIRECTIVE, SCAN_DIRECTIVE

  registered = (
    FROM_DIRECTIVE,
    FROM_ACTIVE_DIRECTIVE,
    SCAN_DIRECTIVE,
    *MUTATION_DIRECTIVES,
    *directives,
  )
  directive_map = {directive.name: directive for directive in registered}
  if len(directive_map) != len(registered):
    raise GraphCompositionError("Graph directive names must be unique.")
  registered_types = (ENTITY_DIRECTIVE, EDGE_DIRECTIVE, *type_directives)
  type_directive_map = {directive.name: directive for directive in registered_types}
  if len(type_directive_map) != len(registered_types):
    raise GraphCompositionError("Graph type directive names must be unique.")
  documents = tuple(parse(module.graphql_schema) for module in modules)
  schema_document = _merge_documents(
    documents,
    tuple(directive_map.values()),
    tuple(type_directive_map.values()),
  )
  try:
    schema = build_ast_schema(schema_document)
  except Exception as exc:
    raise GraphCompositionError(str(exc)) from exc

  type_bindings = _collect_type_bindings(schema_document, type_directive_map)
  entities = {
    type_name: binding.value
    for type_name, bindings_for_type in type_bindings.items()
    if (binding := bindings_for_type.get("entity")) is not None
    and isinstance(binding.value, Entity)
  }
  bindings = _collect_bindings(schema_document, schema, entities, directive_map)
  return MicroGraph(
    schema,
    MappingProxyType(entities),
    MappingProxyType(bindings),
    module_ids,
    MappingProxyType(directive_map),
    MappingProxyType(
      {
        name: MappingProxyType(bindings_for_type)
        for name, bindings_for_type in type_bindings.items()
      }
    ),
  )


def _merge_documents(
  documents: Sequence[DocumentNode],
  directives: Sequence[DirectiveMetadata],
  type_directives: Sequence[TypeDirectiveMetadata],
) -> DocumentNode:
  object_definitions: dict[
    str, list[ObjectTypeDefinitionNode | ObjectTypeExtensionNode]
  ] = defaultdict(list)
  interface_definitions: dict[
    str, list[InterfaceTypeDefinitionNode | InterfaceTypeExtensionNode]
  ] = defaultdict(list)
  input_definitions: dict[
    str, list[InputObjectTypeDefinitionNode | InputObjectTypeExtensionNode]
  ] = defaultdict(list)
  enum_definitions: dict[str, list[EnumTypeDefinitionNode | EnumTypeExtensionNode]] = (
    defaultdict(list)
  )
  union_definitions: dict[
    str, list[UnionTypeDefinitionNode | UnionTypeExtensionNode]
  ] = defaultdict(list)
  schema_definitions: list[SchemaDefinitionNode | SchemaExtensionNode] = []
  other_definitions: dict[tuple[str, str], Node] = {}

  for document in documents:
    for definition in document.definitions:
      if isinstance(definition, ObjectTypeDefinitionNode | ObjectTypeExtensionNode):
        object_definitions[definition.name.value].append(definition)
        continue
      if isinstance(
        definition, InterfaceTypeDefinitionNode | InterfaceTypeExtensionNode
      ):
        interface_definitions[definition.name.value].append(definition)
        continue
      if isinstance(
        definition, InputObjectTypeDefinitionNode | InputObjectTypeExtensionNode
      ):
        input_definitions[definition.name.value].append(definition)
        continue
      if isinstance(definition, EnumTypeDefinitionNode | EnumTypeExtensionNode):
        enum_definitions[definition.name.value].append(definition)
        continue
      if isinstance(definition, UnionTypeDefinitionNode | UnionTypeExtensionNode):
        union_definitions[definition.name.value].append(definition)
        continue
      if isinstance(definition, SchemaDefinitionNode | SchemaExtensionNode):
        schema_definitions.append(definition)
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

  metadata_sdl = "\n".join(
    (
      "scalar GQL",
      "directive @map(key: String!, value: String!) on FIELD_DEFINITION",
      *(item.definition for item in type_directives),
      *(item.definition for item in directives),
    )
  )
  merged: list[Node] = list(parse(metadata_sdl).definitions)
  merged.extend(other_definitions.values())
  if schema_definitions:
    operations: dict[OperationType, Node] = {}
    directive_nodes: dict[str, Node] = {}
    for definition in schema_definitions:
      for operation in definition.operation_types:
        previous = operations.get(operation.operation)
        if previous is not None and print_ast(previous) != print_ast(operation):
          raise GraphCompositionError(
            f"Graph modules define incompatible {operation.operation.value} roots."
          )
        operations[operation.operation] = operation
      for directive in definition.directives or ():
        directive_nodes[print_ast(directive)] = directive
    merged.append(
      SchemaDefinitionNode(
        operation_types=tuple(operations.values()),
        directives=tuple(directive_nodes.values()),
      )
    )
  for name, definitions in object_definitions.items():
    fields: dict[str, FieldDefinitionNode] = {}
    directive_nodes: dict[str, Node] = {}
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
        directive_nodes[print_ast(directive)] = directive
      for interface in definition.interfaces or ():
        interfaces[interface.name.value] = interface
    merged.append(
      ObjectTypeDefinitionNode(
        name=definitions[0].name,
        description=description,
        fields=tuple(fields.values()),
        directives=tuple(directive_nodes.values()),
        interfaces=tuple(interfaces.values()),
      )
    )
  for name, definitions in interface_definitions.items():
    interface_fields: dict[str, Node] = {}
    interfaces: dict[str, NamedTypeNode] = {}
    directive_nodes: dict[str, Node] = {}
    for definition in definitions:
      for field in definition.fields or ():
        _merge_named(
          interface_fields, field, f"interface field {name}.{field.name.value}"
        )
      for interface in definition.interfaces or ():
        interfaces[interface.name.value] = interface
      for directive in definition.directives or ():
        directive_nodes[print_ast(directive)] = directive
    merged.append(
      InterfaceTypeDefinitionNode(
        name=definitions[0].name,
        description=getattr(definitions[0], "description", None),
        fields=tuple(interface_fields.values()),
        interfaces=tuple(interfaces.values()),
        directives=tuple(directive_nodes.values()),
      )
    )
  for name, definitions in input_definitions.items():
    input_fields: dict[str, Node] = {}
    directive_nodes: dict[str, Node] = {}
    for definition in definitions:
      for field in definition.fields or ():
        _merge_named(input_fields, field, f"input field {name}.{field.name.value}")
      for directive in definition.directives or ():
        directive_nodes[print_ast(directive)] = directive
    merged.append(
      InputObjectTypeDefinitionNode(
        name=definitions[0].name,
        description=getattr(definitions[0], "description", None),
        fields=tuple(input_fields.values()),
        directives=tuple(directive_nodes.values()),
      )
    )
  for name, definitions in enum_definitions.items():
    values: dict[str, Node] = {}
    directive_nodes: dict[str, Node] = {}
    for definition in definitions:
      for value in definition.values or ():
        _merge_named(values, value, f"enum value {name}.{value.name.value}")
      for directive in definition.directives or ():
        directive_nodes[print_ast(directive)] = directive
    merged.append(
      EnumTypeDefinitionNode(
        name=definitions[0].name,
        description=getattr(definitions[0], "description", None),
        values=tuple(values.values()),
        directives=tuple(directive_nodes.values()),
      )
    )
  for name, definitions in union_definitions.items():
    types: dict[str, NamedTypeNode] = {}
    directive_nodes: dict[str, Node] = {}
    for definition in definitions:
      for member in definition.types or ():
        types[member.name.value] = member
      for directive in definition.directives or ():
        directive_nodes[print_ast(directive)] = directive
    merged.append(
      UnionTypeDefinitionNode(
        name=definitions[0].name,
        description=getattr(definitions[0], "description", None),
        types=tuple(types.values()),
        directives=tuple(directive_nodes.values()),
      )
    )
  return DocumentNode(definitions=tuple(merged))


def _merge_named(target: dict[str, Node], node: Node, coordinate: str) -> None:
  name = cast(Any, node).name.value
  previous = target.get(name)
  if previous is not None and print_ast(previous) != print_ast(node):
    raise GraphCompositionError(f"Graph modules define incompatible {coordinate}.")
  target[name] = node


def _collect_type_bindings(
  document: DocumentNode,
  directives: Mapping[str, TypeDirectiveMetadata],
) -> dict[str, dict[str, TypeDirectiveBinding]]:
  bindings: dict[str, dict[str, TypeDirectiveBinding]] = {}
  for definition in document.definitions:
    if not isinstance(definition, ObjectTypeDefinitionNode):
      continue
    attached: dict[str, TypeDirectiveBinding] = {}
    declared = {directive.name.value for directive in definition.directives or ()}
    for name in declared & directives.keys():
      metadata = directives[name]
      attached[name] = TypeDirectiveBinding(
        metadata,
        metadata.attach(TypeDirectiveBindContext(definition)),
      )
    if attached:
      bindings[definition.name.value] = attached
  return bindings


def _attach_entity(context: TypeDirectiveBindContext) -> Entity:
  definition = context.type
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
  declared_fields = {field.name.value for field in definition.fields or ()}
  if len(keys) != 1:
    raise GraphCompositionError(
      f"Entity {definition.name.value} must declare exactly one canonical key."
    )
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
  maps: list[tuple[str, str, str]] = []
  for field in definition.fields or ():
    for directive in field.directives or ():
      if directive.name.value != "map":
        continue
      scalars = {
        argument.name.value: argument.value.value
        for argument in directive.arguments or ()
        if isinstance(argument.value, StringValueNode | EnumValueNode)
      }
      if set(scalars) != {"key", "value"} or not all(
        name in MAP_SCALARS for name in scalars.values()
      ):
        raise GraphCompositionError(
          f"{definition.name.value}.{field.name.value}: @map(key:, value:) takes "
          f"scalars: {', '.join(MAP_SCALARS)}."
        )
      maps.append((field.name.value, scalars["key"], scalars["value"]))
  return Entity(
    definition.name.value, tuple(keys), frozenset(declared_fields), tuple(maps)
  )


MAP_SCALARS = ("String", "ID", "Int", "Float", "Boolean")
# What a map's keys and values may be declared as.


def _matches(scalar: str, value: object) -> bool:
  if scalar in ("String", "ID"):
    return isinstance(value, str)
  if scalar == "Boolean":
    return isinstance(value, bool)
  if scalar == "Int":
    return isinstance(value, int) and not isinstance(value, bool)
  return isinstance(value, int | float) and not isinstance(value, bool)


def check_map(entity: Entity, field: str, patch: object) -> None:
  """Raise ValueError unless every key and value of `patch` (a dict, or for a removal a
  list of keys) is of the type the field's `@map` declares."""
  declared = next((m for m in entity.maps if m[0] == field), None)
  if declared is None or patch is None:
    return
  _, key_scalar, value_scalar = declared
  if isinstance(patch, list):
    entries: list[tuple[object, object | None]] = [(key, None) for key in patch]
  elif isinstance(patch, dict):
    entries = list(patch.items())
  else:
    raise ValueError(f"{entity.name}.{field} is a map: pass an object.")  # noqa: TRY004
  for key, value in entries:
    if key_scalar not in ("String", "ID"):
      try:
        {
          "Int": int,
          "Float": float,
          "Boolean": lambda k: {"true": True, "false": False}[k],
        }[key_scalar](key)
      except ValueError, KeyError, TypeError:
        raise ValueError(
          f"{entity.name}.{field}: key {key!r} is not a {key_scalar}."
        ) from None
    elif not isinstance(key, str):
      raise ValueError(f"{entity.name}.{field}: key {key!r} is not a {key_scalar}.")
    if value is not None and not _matches(value_scalar, value):
      raise ValueError(
        f"{entity.name}.{field}[{key!r}]: {value!r} is not a {value_scalar}."
      )


@dataclass(frozen=True, slots=True)
class EdgeType:
  """An object type that is one keyed entry of an entity's list: its fields are the
  edge's own properties, and `target` names the field that is the entity it points at."""

  name: str
  target: str


def _attach_edge(context: TypeDirectiveBindContext) -> EdgeType:
  definition = context.type
  directive = next(
    item for item in definition.directives or () if item.name.value == "edge"
  )
  target = next(
    (
      argument.value.value
      for argument in directive.arguments or ()
      if argument.name.value == "target" and isinstance(argument.value, StringValueNode)
    ),
    None,
  )
  declared = {field.name.value for field in definition.fields or ()}
  if target is None or target not in declared:
    raise GraphCompositionError(
      f"@edge on {definition.name.value} must name one of its fields as target."
    )
  return EdgeType(definition.name.value, target)


EDGE_DIRECTIVE = TypeDirectiveMetadata(
  "edge",
  "directive @edge(target: String!) on OBJECT",
  _attach_edge,
)

ENTITY_DIRECTIVE = TypeDirectiveMetadata(
  "entity",
  "directive @entity(key: [String!]!) repeatable on OBJECT",
  _attach_entity,
)


def _collect_bindings(
  document: DocumentNode,
  schema: GraphQLSchema,
  entities: Mapping[str, Entity],
  directives: Mapping[str, DirectiveMetadata],
) -> dict[tuple[str, str], DirectiveBinding]:
  root_names = {
    schema.query_type.name if schema.query_type else "": OperationType.QUERY,
    schema.mutation_type.name if schema.mutation_type else "": OperationType.MUTATION,
    schema.subscription_type.name
    if schema.subscription_type
    else "": OperationType.SUBSCRIPTION,
  }
  bindings: dict[tuple[str, str], DirectiveBinding] = {}
  for definition in document.definitions:
    if not isinstance(definition, ObjectTypeDefinitionNode):
      continue
    operation = root_names.get(definition.name.value)
    for field in definition.fields or ():
      return_type = _named_type(field.type)
      entity = entities.get(return_type)
      declared = [
        item for item in field.directives or () if item.name.value in directives
      ]
      if operation is not None and entity is not None and not declared:
        raise GraphCompositionError(
          f"{definition.name.value}.{field.name.value} returns entity {entity.name} "
          "but does not declare @from."
        )
      if not declared:
        continue
      if len(declared) != 1:
        raise GraphCompositionError(
          f"{definition.name.value}.{field.name.value} must declare exactly one "
          "registered runtime directive."
        )
      directive_node = declared[0]
      metadata = directives[directive_node.name.value]
      if operation is not None and operation not in metadata.operations:
        raise GraphCompositionError(
          f"@{metadata.name} does not support {operation.value} operations."
        )
      value = metadata.bind(
        DirectiveBindContext(
          operation,
          definition.name.value,
          field,
          return_type,
          entity,
          entities,
        )
      )
      bindings[(definition.name.value, field.name.value)] = DirectiveBinding(
        metadata,
        value,
        return_type,
      )
  return bindings


def _compile_key(value: Node, arguments: set[str], directive: str) -> KeyBinding:
  if not isinstance(value, ObjectValueNode):
    raise GraphCompositionError(f"@{directive} key must be an object.")
  fields: list[tuple[str, str]] = []
  for field in value.fields:
    if not isinstance(field.value, EnumValueNode | StringValueNode):
      raise GraphCompositionError(
        f"@{directive} key values must name GraphQL arguments."
      )
    fields.append((field.name.value, field.value.value))
  if not fields:
    raise GraphCompositionError(f"@{directive} key cannot be empty.")
  unknown = {argument for _, argument in fields} - arguments
  if unknown:
    raise GraphCompositionError(
      f"@{directive} references unknown arguments: {', '.join(sorted(unknown))}."
    )
  return KeyBinding(tuple(fields))


def _attach_from(context: DirectiveBindContext) -> FromDirective:
  if context.operation is not OperationType.QUERY:
    raise GraphCompositionError("@from supports Query fields only.")
  if context.entity is None or not isinstance(context.entity, Entity):
    raise GraphCompositionError(
      f"{context.parent_type}.{context.field.name.value} declares @from but does "
      "not return an entity."
    )
  if _is_list_type(context.field.type):
    raise GraphCompositionError(
      f"{context.parent_type}.{context.field.name.value} uses @from but returns a list."
    )
  directive = next(
    item for item in context.field.directives or () if item.name.value == "from"
  )
  key_argument = next(
    (
      argument for argument in directive.arguments or () if argument.name.value == "key"
    ),
    None,
  )
  if key_argument is None:
    raise GraphCompositionError("@from requires a key.")
  expression = _compile_key(
    key_argument.value,
    {argument.name.value for argument in context.field.arguments or ()},
    "from",
  )
  if expression.key_fields not in context.entity.keys:
    raise GraphCompositionError(
      f"The @from key on {context.parent_type}.{context.field.name.value} does "
      f"not match an @entity key on {context.entity.name}."
    )
  return FromDirective(context.entity, expression)


def _compile_from(context: DirectiveCompileContext) -> DirectiveResult:
  from .._compiler import entity_identity, physical_type

  binding = context.binding
  if not isinstance(binding, FromDirective):
    raise TypeError("@from received invalid attached metadata.")
  key = binding.expression.evaluate(context.arguments)
  parameter = f"{context.parameter_prefix}_identity"
  return DirectiveResult(
    (
      f"OPTIONAL MATCH ({context.variable}:{physical_type(binding.entity.name)})",
      f"WHERE {context.variable}._micro_id = ${parameter}",
    ),
    {parameter: entity_identity(binding.entity.name, key)},
    binding.entity.name,
  )


FROM_DIRECTIVE = DirectiveMetadata(
  "from",
  "directive @from(key: GQL!) on FIELD_DEFINITION",
  _attach_from,
  _compile_from,
  frozenset((OperationType.QUERY,)),
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
