import pytest
from graphql import GraphQLError
from starlette.testclient import TestClient

from micro.store import (
  GraphResult,
  GraphStatement,
  Store,
  StoreModule,
)


class Executor:
  def __init__(self) -> None:
    self.started = False
    self.closed = False
    self.statements: list[GraphStatement] = []

  async def start(self) -> None:
    self.started = True

  async def execute(self, statement: GraphStatement) -> GraphResult:
    self.statements.append(statement)
    values = ("person:Ada", "Ada")
    return GraphResult((dict(zip(statement.columns, values, strict=True)),))

  async def close(self) -> None:
    self.closed = True


PEOPLE = StoreModule(
  id="people",
  schema="""
    type Person @entity(key: ["name"]) { name: String! }
    type Query {
      person(name: String!): Person @from(key: "{'name': name}")
    }
  """,
)


def activate(client: TestClient, module: StoreModule = PEOPLE) -> None:
  response = client.post(
    "/topology",
    json={"revision": 0, "modules": [module.model_dump(by_alias=True)]},
  )
  assert response.status_code == 204


def test_store_executes_compiled_graphql_operation() -> None:
  executor = Executor()
  store = Store(executor=executor)

  with TestClient(store) as client:
    activate(client)
    assert client.get("/health/ready").status_code == 204
    response = client.post(
      "/graphql",
      json={
        "query": "query Person($name: String!) { person(name: $name) { name } }",
        "variables": {"name": "Ada"},
      },
    )

  assert response.status_code == 200
  assert response.json() == {"data": {"person": {"name": "Ada"}}}
  assert executor.started
  assert executor.closed
  assert executor.statements[0].columns == ("c0", "c1")


def test_store_serves_graphql_introspection_without_using_database() -> None:
  executor = Executor()
  store = Store(executor=executor)

  with TestClient(store) as client:
    activate(client)
    response = client.post(
      "/graphql",
      json={"query": "{ __schema { queryType { name } } }"},
    )

  assert response.status_code == 200
  assert response.json() == {"data": {"__schema": {"queryType": {"name": "Query"}}}}
  assert executor.statements == []


def test_store_rejects_invalid_graphql_before_compilation() -> None:
  executor = Executor()
  store = Store(executor=executor)

  with TestClient(store) as client:
    activate(client)
    response = client.post("/graphql", json={"query": "{ missing }"})

  assert response.status_code == 400
  assert response.json()["errors"]
  assert executor.statements == []


def test_graph_statement_requires_valid_gql() -> None:
  with pytest.raises(ValueError, match="valid ISO GQL"):
    GraphStatement("this is not gql")


def test_store_returns_explicit_graphql_errors() -> None:
  class FailingExecutor(Executor):
    async def execute(self, statement: GraphStatement) -> GraphResult:
      raise GraphQLError("Operation is unavailable.")

  store = Store(executor=FailingExecutor())

  with TestClient(store) as client:
    activate(client)
    response = client.post(
      "/graphql",
      json={"query": '{ person(name: "Ada") { name } }'},
    )

  assert response.status_code == 200
  assert response.json() == {
    "data": None,
    "errors": [{"message": "Operation is unavailable."}],
  }


def test_overseer_topology_activates_distributed_store_module() -> None:
  module = StoreModule(
    id="example.status",
    schema="""
      type Status @entity(key: ["value"]) { value: String! }
      type Query {
        moduleStatus(value: String!): Status @from(key: "{'value': value}")
      }
    """,
  )
  store = Store(executor=Executor())

  with TestClient(store) as client:
    assert (
      client.post("/graphql", json={"query": "{ moduleStatus }"}).status_code == 400
    )
    activated = client.post(
      "/topology",
      json={"revision": 0, "modules": [module.model_dump(by_alias=True)]},
    )
    response = client.post(
      "/graphql", json={"query": "{ moduleStatus(value: \"Ada\") { value } }"}
    )

  assert activated.status_code == 204
  assert response.json() == {"data": {"moduleStatus": {"value": "Ada"}}}
  assert store.active_modules == ("example.status",)
  assert store.topology_revision == 0


def test_store_becomes_unavailable_for_an_uncomposable_topology() -> None:
  store = Store(executor=Executor())

  with TestClient(store) as client:
    response = client.post(
      "/topology",
      json={
        "revision": 0,
        "modules": [
          {
            "id": "example.status",
            "schema": """
              type Status @entity(key: [\"id\"]) { id: ID! }
              type Query { status(id: ID!): Status }
            """,
          }
        ],
      },
    )
    ready = client.get("/health/ready")
    graphql = client.post(
      "/graphql", json={"query": "{ person(name: \"Ada\") { name } }"}
    )

  assert response.status_code == 409
  assert ready.status_code == 503
  assert graphql.status_code == 503
  assert store.active_modules == ()
  assert store.topology_revision == -1
  assert store.desired_topology_revision == 0
  assert store.composition_error is not None


def test_store_can_retry_a_failed_desired_revision() -> None:
  store = Store(executor=Executor())
  invalid = StoreModule(
    id="people",
    schema="""
      type Person @entity(key: ["name"]) { name: String! }
      type Query { person(name: String!): Person }
    """,
  )
  valid = StoreModule(
    id="people",
    schema="""
      type Person @entity(key: ["name"]) { name: String! }
      type Query {
        person(name: String!): Person @from(key: "{'name': name}")
      }
    """,
  )

  with TestClient(store) as client:
    rejected = client.post(
      "/topology",
      json={"revision": 0, "modules": [invalid.model_dump(by_alias=True)]},
    )
    recovered = client.post(
      "/topology",
      json={"revision": 0, "modules": [valid.model_dump(by_alias=True)]},
    )

  assert rejected.status_code == 409
  assert recovered.status_code == 204
  assert store.topology_revision == 0
  assert store.composition_error is None
