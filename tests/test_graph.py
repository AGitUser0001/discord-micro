from types import MappingProxyType

import pytest
from graphql import GraphQLObjectType, get_operation_ast, parse
from starlette.testclient import TestClient

from micro.store import (
  GraphCompositionError,
  GraphModule,
  GraphQLRequest,
  GraphResult,
  GraphStatement,
  MicroGraphCompiler,
  Store,
  compose_graph,
  entity_identity,
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
      guild(id: ID!): Guild @from(key: "{'id': id}")
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
        guild(name: String!): Guild @from(key: "{'name': name}")
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

  compiled = MicroGraphCompiler(graph).compile(request)

  assert f":{physical_type('Guild')}" in compiled.statement.text
  assert f":{physical_reference('Guild.channels')}" in compiled.statement.text
  assert compiled.statement.parameters == {
    "root_identity": entity_identity("Guild", {"id": "123"})
  }
  columns = compiled.statement.columns
  assert compiled.shape(
    GraphResult(
      (
        dict(
          zip(
            columns, ("guild:123", "123", "Micro", "channel:1", "1", "one"), strict=True
          )
        ),
        dict(
          zip(
            columns, ("guild:123", "123", "Micro", "channel:2", "2", "two"), strict=True
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


def test_store_uses_graph_compiler_without_application_compiler() -> None:
  class Executor:
    async def start(self) -> None:
      pass

    async def execute(self, statement: GraphStatement) -> GraphResult:
      return GraphResult(
        (
          dict(
            zip(
              statement.columns,
              ("guild:123", "123", "Micro"),
              strict=True,
            )
          ),
        )
      )

    async def close(self) -> None:
      pass

  store = Store(executor=Executor())
  with TestClient(store) as client:
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
