from types import MappingProxyType
from typing import cast

import pytest
from conftest import EngineHarness
from graphql import (
  GraphQLEnumType,
  GraphQLError,
  GraphQLInputObjectType,
  GraphQLObjectType,
  GraphQLUnionType,
  get_operation_ast,
  parse,
)
from pydantic import JsonValue

from micro.store import (
  DirectiveBindContext,
  DirectiveCompileContext,
  DirectiveMetadata,
  DirectiveResult,
  GraphBatch,
  GraphBatchResult,
  GraphCompiler,
  GraphCompositionError,
  GraphLayout,
  GraphModule,
  GraphQLRequest,
  GraphResult,
  compose_graph,
  entity_identity,
  physical_field,
  physical_reference,
  physical_type,
)

GUILDS = GraphModule(
  id="guilds",
  schema="""
    type Guild @entity(key: ["id"]) {
      id: ID!
      name: String!
    }

    type Query {
      guild(id: ID!): Guild @from(key: {id: id})
    }
  """,
)

CHANNELS = GraphModule(
  id="channels",
  schema="""
    type Guild @entity(key: ["id"]) {
      id: ID!
      channels: [Channel!]!
    }

    type Channel @entity(key: ["id"]) {
      id: ID!
      name: String!
    }
  """,
)


def test_graph_composes_shared_entity_and_query_fields() -> None:
  graph = compose_graph((GUILDS, CHANNELS))

  guild = graph.schema.get_type("Guild")
  assert isinstance(guild, GraphQLObjectType)
  assert set(guild.fields) == {"id", "name", "channels"}
  assert graph.entities["Guild"].keys == (("id",),)
  assert graph.type_bindings["Guild"]["entity"].value == graph.entities["Guild"]


def test_graph_requires_explicit_entity_lookup() -> None:
  module = GraphModule(
    id="guilds",
    schema="""
      type Guild @entity(key: ["id"]) { id: ID! }
      type Query { guild(id: ID!): Guild }
    """,
  )

  with pytest.raises(GraphCompositionError, match="does not declare @from"):
    compose_graph((module,))


def test_from_expression_must_match_an_entity_key() -> None:
  module = GraphModule(
    id="guilds",
    schema="""
      type Guild @entity(key: ["id"]) { id: ID! }
      type Query {
        guild(name: String!): Guild @from(key: {name: name})
      }
    """,
  )

  with pytest.raises(GraphCompositionError, match="does not match an @entity key"):
    compose_graph((module,))


def test_compiler_uses_hashed_paths_and_shapes_entity_lists() -> None:
  graph = compose_graph((GUILDS, CHANNELS))
  document = parse(
    """
      query Guild($id: ID!) {
        guild(id: $id) {
          id
          name
          channels { id name }
        }
      }
    """
  )
  operation = get_operation_ast(document)
  assert operation is not None
  request = GraphQLRequest(
    graph.schema,
    document,
    operation,
    MappingProxyType({"id": "123"}),
    "Guild",
  )

  compiled = GraphCompiler(graph).compile(request)

  statement = compiled.batch.statements[0]
  assert f":{physical_type('Guild')}" in statement.text
  assert f":{physical_reference('Guild.channels')}" in statement.text
  assert statement.parameters == {
    "p0_identity": entity_identity("Guild", {"id": "123"})
  }
  columns = statement.columns
  assert compiled.shape(
    GraphBatchResult(
      (
        GraphResult(
          (
            dict(
              zip(
                columns,
                ("guild:123", "123", "Micro", "channel:1", "1", "one"),
                strict=True,
              )
            ),
            dict(
              zip(
                columns,
                ("guild:123", "123", "Micro", "channel:2", "2", "two"),
                strict=True,
              )
            ),
          )
        ),
      )
    )
  ) == {
    "guild": {
      "id": "123",
      "name": "Micro",
      "channels": [
        {"id": "1", "name": "one"},
        {"id": "2", "name": "two"},
      ],
    }
  }


def test_physical_names_are_stable_and_coordinate_specific() -> None:
  assert physical_reference("Guild.channels") == physical_reference("Guild.channels")
  assert physical_reference("Guild.channels") != physical_reference("Category.channels")


def test_scan_compiles_bounded_pagination() -> None:
  module = GraphModule(
    id="guild-scan",
    schema="""
      type Guild @entity(key: ["id"]) { id: ID! }
      type Query {
        guilds(first: Int!, offset: Int!): [Guild!]! @scan
      }
    """,
  )
  graph = compose_graph((module,))
  document = parse("{ guilds(first: 25, offset: 50) { id } }")
  operation = get_operation_ast(document)
  assert operation is not None

  compiled = GraphCompiler(graph).compile(
    GraphQLRequest(graph.schema, document, operation, MappingProxyType({}), None)
  )
  statement = compiled.batch.statements[0]

  assert "ORDER BY n0._micro_id SKIP $p0_offset LIMIT $p0_first" in statement.text
  assert statement.parameters == {"p0_first": 25, "p0_offset": 50}


def test_scan_rejects_unbounded_pages() -> None:
  module = GraphModule(
    id="guild-scan",
    schema="""
      type Guild @entity(key: ["id"]) { id: ID! }
      type Query { guilds(first: Int!, offset: Int!): [Guild!]! @scan }
    """,
  )
  graph = compose_graph((module,))
  document = parse("{ guilds(first: 1001, offset: 0) { id } }")
  operation = get_operation_ast(document)
  assert operation is not None

  with pytest.raises(GraphQLError, match="first must be between"):
    GraphCompiler(graph).compile(
      GraphQLRequest(graph.schema, document, operation, MappingProxyType({}), None)
    )


def test_store_uses_graph_compiler_without_application_compiler() -> None:
  class Executor:
    async def start(self) -> None:
      pass

    async def execute(self, batch: GraphBatch) -> GraphBatchResult:
      statement = batch.statements[-1]
      return GraphBatchResult(
        (
          GraphResult(
            (
              dict(
                zip(
                  statement.columns,
                  ("guild:123", "123", "Micro"),
                  strict=True,
                )
              ),
            )
          ),
        )
      )

    async def apply_layout(self, layout: GraphLayout) -> None:
      pass

    async def close(self) -> None:
      pass

  store = EngineHarness(Executor())
  with store as client:
    topology = client.post(
      "/topology",
      json={"revision": 0, "modules": [GUILDS.model_dump(by_alias=True)]},
    )
    response = client.post(
      "/graphql",
      json={"query": '{ guild(id: "123") { id name } }'},
    )

  assert topology.status_code == 204
  assert response.json() == {"data": {"guild": {"id": "123", "name": "Micro"}}}


def test_compiler_supports_multiple_roots_fragments_typename_and_conditionals() -> None:
  graph = compose_graph((GUILDS,))
  document = parse(
    """
      query Guilds($second: Boolean!) {
        first: guild(id: "1") { ...GuildFields }
        second: guild(id: "2") @include(if: $second) { ...GuildFields }
      }

      fragment GuildFields on Guild {
        __typename
        id
        ... on Guild { name }
      }
    """
  )
  operation = get_operation_ast(document, "Guilds")
  assert operation is not None
  compiled = GraphCompiler(graph).compile(
    GraphQLRequest(
      graph.schema,
      document,
      operation,
      MappingProxyType({"second": True}),
      "Guilds",
    )
  )
  statement = compiled.batch.statements[0]
  columns = statement.columns

  assert statement.parameters == {
    "p0_identity": entity_identity("Guild", {"id": "1"}),
    "p1_identity": entity_identity("Guild", {"id": "2"}),
  }
  assert compiled.shape(
    GraphBatchResult(
      (
        GraphResult(
          (
            dict(
              zip(
                columns,
                ("guild:1", "Guild", "1", "one", "guild:2", "Guild", "2", "two"),
                strict=True,
              )
            ),
          )
        ),
      )
    )
  ) == {
    "first": {"__typename": "Guild", "id": "1", "name": "one"},
    "second": {"__typename": "Guild", "id": "2", "name": "two"},
  }

  skipped = GraphCompiler(graph).compile(
    GraphQLRequest(
      graph.schema,
      document,
      operation,
      MappingProxyType({"second": False}),
      "Guilds",
    )
  )
  assert set(skipped.batch.statements[0].parameters) == {"p0_identity"}
  assert set(skipped.shape(GraphBatchResult((GraphResult(()),)))) == {"first"}


def test_registered_directive_attaches_metadata_and_compiles_mutation_scalar() -> None:
  def attach(context: DirectiveBindContext) -> str:
    return context.field.name.value

  def compile(context: DirectiveCompileContext) -> DirectiveResult:
    parameter = f"{context.parameter_prefix}_value"
    return DirectiveResult(
      (),
      {parameter: cast(JsonValue, context.arguments["value"])},
      "",
      f"${parameter}",
    )

  constant = DirectiveMetadata(
    "constant",
    "directive @constant on FIELD_DEFINITION",
    attach,
    compile,
  )
  module = GraphModule(
    id="mutation",
    schema="""
      type Query { noop: Boolean }
      type Mutation { set(value: String!): String! @constant }
    """,
  )
  graph = compose_graph((module,), directives=(constant,))
  document = parse('mutation { set(value: "updated") }')
  operation = get_operation_ast(document)
  assert operation is not None
  compiled = GraphCompiler(graph).compile(
    GraphQLRequest(
      graph.schema,
      document,
      operation,
      MappingProxyType({}),
      None,
    )
  )

  assert graph.bindings[("Mutation", "set")].value == "set"
  assert compiled.batch.statements[0].parameters == {"p0_value": "updated"}
  assert compiled.shape(GraphBatchResult((GraphResult(({"c0": "updated"},)),))) == {
    "set": "updated"
  }


def test_builtin_mutation_directives_compile_entity_and_relationship_writes() -> None:
  module = GraphModule(
    id="mutations",
    schema="""
      type Guild @entity(key: ["id"]) {
        id: ID!
        name: String!
        remaining: Int!
        channels: [Channel!]!
      }
      type Channel @entity(key: ["id"]) { id: ID!, name: String! }
      type Query { guild(id: ID!): Guild @from(key: {id: id}) }
      type Mutation {
        insertGuild(id: ID!, name: String!): Guild!
          @insert(key: {id: id}, set: {id: id, name: name})
        updateGuild(id: ID!, name: String!): Guild
          @update(key: {id: id}, set: {name: name})
        decrementGuild(id: ID!): Guild
          @update(
            key: {id: "id"}
            where: "current.remaining > 0"
            set: {remaining: "current.remaining - 1"}
          )
        deleteGuild(id: ID!): Boolean!
          @delete(type: "Guild", key: {id: id})
        connectChannel(guild: ID!, channel: ID!): Boolean!
          @connect(
            fromType: "Guild", fromKey: {id: guild},
            toType: "Channel", toKey: {id: channel}, field: "channels"
          )
        disconnectChannel(guild: ID!, channel: ID!): Boolean!
          @disconnect(
            fromType: "Guild", fromKey: {id: guild},
            toType: "Channel", toKey: {id: channel}, field: "channels"
          )
      }
    """,
  )
  graph = compose_graph((module,))

  def compile(query: str):
    document = parse(query)
    operation = get_operation_ast(document)
    assert operation is not None
    return GraphCompiler(graph).compile(
      GraphQLRequest(graph.schema, document, operation, MappingProxyType({}), None)
    )

  inserted = compile(
    'mutation { insertGuild(id: "1", name: "Micro") { id name } }'
  ).batch.statements[0]
  updated = compile(
    'mutation { updateGuild(id: "1", name: "Updated") { name } }'
  ).batch.statements[0]
  decremented = compile(
    'mutation { decrementGuild(id: "1") { remaining } }'
  ).batch.statements[0]
  deleted = compile('mutation { deleteGuild(id: "1") }').batch.statements[0]
  connected = compile(
    'mutation { connectChannel(guild: "1", channel: "2") }'
  ).batch.statements[0]
  disconnected = compile(
    'mutation { disconnectChannel(guild: "1", channel: "2") }'
  ).batch.statements[0]

  assert "INSERT" in inserted.text
  assert physical_type("Guild") in inserted.text
  assert physical_field("Guild.name") in inserted.text
  assert "SET" in updated.text
  assert f"n0.{physical_field('Guild.remaining')} > 0" in decremented.text
  assert f"n0.{physical_field('Guild.remaining')} - 1" in decremented.text
  assert "DETACH DELETE" in deleted.text
  assert f"[:{physical_reference('Guild.channels')}]" in connected.text
  assert "DELETE" in disconnected.text


def test_composer_merges_all_extensible_graphql_type_kinds() -> None:
  core = GraphModule(
    id="core",
    schema="""
      schema { query: Root }
      interface Node { id: ID! }
      input Filter { term: String }
      enum Kind { A }
      type A implements Node @entity(key: ["id"]) { id: ID! }
      union Result = A
      type Root {
        a(id: ID!): A @from(key: {id: id})
      }
    """,
  )
  extension = GraphModule(
    id="extension",
    schema="""
      extend interface Node { name: String! }
      extend input Filter { limit: Int }
      extend enum Kind { B }
      extend type A { name: String! }
      type B implements Node @entity(key: ["id"]) {
        id: ID!
        name: String!
      }
      extend union Result = B
      extend type Root {
        b(id: ID!): B @from(key: {id: id})
      }
    """,
  )

  graph = compose_graph((core, extension))

  assert graph.schema.query_type is not None
  assert graph.schema.query_type.name == "Root"
  assert set(graph.schema.query_type.fields) == {"a", "b"}
  filter_type = graph.schema.get_type("Filter")
  kind_type = graph.schema.get_type("Kind")
  result_type = graph.schema.get_type("Result")
  assert isinstance(filter_type, GraphQLInputObjectType)
  assert isinstance(kind_type, GraphQLEnumType)
  assert isinstance(result_type, GraphQLUnionType)
  assert set(filter_type.fields) == {"term", "limit"}
  assert set(kind_type.values) == {"A", "B"}
  assert set(result_type.types) == {
    graph.schema.get_type("A"),
    graph.schema.get_type("B"),
  }
