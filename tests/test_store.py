from collections.abc import Mapping, Sequence

import pytest
from graphql import GraphQLError
from starlette.testclient import TestClient

from micro.service import JsonValue
from micro.store import (
  CompiledOperation,
  GraphCompiler,
  GraphQLRequest,
  GraphResult,
  GraphStatement,
  Store,
  StoreModule,
)


class Compiler:
  def compile(self, request: GraphQLRequest) -> CompiledOperation:
    name = request.variables["name"]
    statement = GraphStatement(
      "MATCH (person:Person) WHERE person.name = $name RETURN person.name AS name",
      {"name": name},
      ("name",),
    )

    def shape(result: GraphResult) -> Mapping[str, JsonValue]:
      return {"person": dict(result.rows[0]) if result.rows else None}

    return CompiledOperation(statement, shape)


class Executor:
  def __init__(self) -> None:
    self.started = False
    self.closed = False
    self.statements: list[GraphStatement] = []

  async def start(self) -> None:
    self.started = True

  async def execute(self, statement: GraphStatement) -> GraphResult:
    self.statements.append(statement)
    return GraphResult(({"name": statement.parameters["name"]},))

  async def close(self) -> None:
    self.closed = True


SCHEMA = """
  type Person { name: String! }
  type Query { person(name: String!): Person }
"""


def test_store_executes_compiled_graphql_operation() -> None:
  executor = Executor()
  store = Store(SCHEMA, compiler=Compiler(), executor=executor)

  with TestClient(store) as client:
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
  assert executor.statements[0].parameters == {"name": "Ada"}


def test_store_serves_graphql_introspection_without_using_database() -> None:
  executor = Executor()
  store = Store(SCHEMA, compiler=Compiler(), executor=executor)

  with TestClient(store) as client:
    response = client.post(
      "/graphql",
      json={"query": "{ __schema { queryType { name } } }"},
    )

  assert response.status_code == 200
  assert response.json() == {"data": {"__schema": {"queryType": {"name": "Query"}}}}
  assert executor.statements == []


def test_store_rejects_invalid_graphql_before_compilation() -> None:
  executor = Executor()
  store = Store(SCHEMA, compiler=Compiler(), executor=executor)

  with TestClient(store) as client:
    response = client.post("/graphql", json={"query": "{ missing }"})

  assert response.status_code == 400
  assert response.json()["errors"]
  assert executor.statements == []


def test_graph_statement_requires_valid_gql() -> None:
  with pytest.raises(ValueError, match="valid ISO GQL"):
    GraphStatement("this is not gql")


def test_store_returns_explicit_graphql_errors() -> None:
  class FailingCompiler:
    def compile(self, request: GraphQLRequest) -> CompiledOperation:
      raise GraphQLError("Operation is unavailable.")

  store = Store(SCHEMA, compiler=FailingCompiler(), executor=Executor())

  with TestClient(store) as client:
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
  class ModuleCompiler:
    def compile(self, request: GraphQLRequest) -> CompiledOperation:
      statement = GraphStatement("RETURN 'active' AS status", columns=("status",))
      return CompiledOperation(
        statement,
        lambda result: {"moduleStatus": result.rows[0]["status"]},
      )

  class ModuleExecutor(Executor):
    async def execute(self, statement: GraphStatement) -> GraphResult:
      self.statements.append(statement)
      return GraphResult(({"status": "active"},))

  class Composer:
    def compose(
      self, base: GraphCompiler, modules: Sequence[StoreModule]
    ) -> ModuleCompiler:
      assert tuple(modules) == (module,)
      return ModuleCompiler()

  module = StoreModule(
    id="example.status",
    schema="extend type Query { moduleStatus: String! }",
  )
  store = Store(
    SCHEMA,
    compiler=Compiler(),
    executor=ModuleExecutor(),
    module_composer=Composer(),
  )

  with TestClient(store) as client:
    assert (
      client.post("/graphql", json={"query": "{ moduleStatus }"}).status_code == 400
    )
    activated = client.post(
      "/topology",
      json={"revision": 0, "modules": [module.model_dump(by_alias=True)]},
    )
    response = client.post("/graphql", json={"query": "{ moduleStatus }"})

  assert activated.status_code == 204
  assert response.json() == {"data": {"moduleStatus": "active"}}
  assert store.active_modules == ("example.status",)
  assert store.topology_revision == 0


def test_store_becomes_unavailable_for_an_uncomposable_topology() -> None:
  store = Store(SCHEMA, compiler=Compiler(), executor=Executor())

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
  store = Store(SCHEMA, compiler=Compiler(), executor=Executor())
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
