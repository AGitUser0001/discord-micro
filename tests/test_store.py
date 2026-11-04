import asyncio

import pytest
from conftest import EngineHarness
from graphql import GraphQLError

from micro.store import (
  GraphBatch,
  GraphBatchResult,
  GraphLayout,
  GraphModule,
  GraphResult,
  GraphStatement,
  Store,
  StoreClient,
)


class Executor:
  def __init__(self) -> None:
    self.started = False
    self.closed = False
    self.statements: list[GraphStatement] = []

  async def start(self) -> None:
    self.started = True

  async def execute(self, batch: GraphBatch) -> GraphBatchResult:
    self.statements.extend(batch.statements)
    statement = batch.statements[-1]
    values = ("person:Ada", "Ada")
    return GraphBatchResult(
      (GraphResult((dict(zip(statement.columns, values, strict=True)),)),)
    )

  async def apply_layout(self, layout: GraphLayout) -> None:
    pass

  async def close(self) -> None:
    self.closed = True


PEOPLE = GraphModule(
  id="people",
  schema="""
    type Person @entity(key: ["name"]) { name: String! }
    type Query {
      person(name: String!): Person @from(key: {name: name})
    }
  """,
)


def activate(client: EngineHarness, module: GraphModule = PEOPLE) -> None:
  response = client.post(
    "/topology", json={"modules": [module.model_dump(by_alias=True)]}
  )
  assert response.status_code == 204


def test_engine_executes_compiled_graphql_operation() -> None:
  executor = Executor()
  with EngineHarness(executor) as client:
    activate(client)
    response = client.post(
      "/graphql",
      json={
        "query": "query Person($name: String!) { person(name: $name) { name } }",
        "variables": {"name": "Ada"},
      },
    )
  assert response.json() == {"data": {"person": {"name": "Ada"}}}
  assert executor.started and executor.closed
  assert executor.statements[0].columns == ("c0", "c1")


def test_engine_serves_introspection_without_using_database() -> None:
  executor = Executor()
  with EngineHarness(executor) as client:
    activate(client)
    response = client.post(
      "/graphql", json={"query": "{ __schema { queryType { name } } }"}
    )
  assert response.json() == {"data": {"__schema": {"queryType": {"name": "Query"}}}}
  assert executor.statements == []


def test_engine_rejects_invalid_graphql_before_compilation() -> None:
  executor = Executor()
  with EngineHarness(executor) as client:
    activate(client)
    response = client.post("/graphql", json={"query": "{ missing }"})
  assert response.json()["errors"]  # type: ignore[index]
  assert executor.statements == []


def test_graph_statement_requires_valid_gql() -> None:
  with pytest.raises(ValueError, match="valid ISO GQL"):
    GraphStatement("this is not gql")


def test_engine_returns_explicit_graphql_errors() -> None:
  class FailingExecutor(Executor):
    async def execute(self, batch: GraphBatch) -> GraphBatchResult:
      raise GraphQLError("Operation is unavailable.")

  with EngineHarness(FailingExecutor()) as client:
    activate(client)
    response = client.post(
      "/graphql", json={"query": '{ person(name: "Ada") { name } }'}
    )
  assert response.json() == {
    "data": None,
    "errors": [{"message": "Operation is unavailable."}],
  }


def test_engine_keeps_its_last_good_graph_when_a_new_module_set_fails() -> None:
  invalid = GraphModule(
    id="people",
    schema="""
      type Person @entity(key: ["name"]) { name: String! }
      type Query { person(name: String!): Person }
    """,
  )
  with EngineHarness(Executor()) as client:
    activate(client)
    rejected = client.post(
      "/topology", json={"modules": [invalid.model_dump(by_alias=True)]}
    )
    assert rejected.status_code == 409
    assert client.engine.available
    assert client.engine.composition_error is not None
    still = client.post("/graphql", json={"query": '{ person(name: "Ada") { name } }'})
    assert still.json() == {"data": {"person": {"name": "Ada"}}}
    activate(client)
    assert client.engine.composition_error is None


def test_store_service_composes_modules_declared_by_services(nats_url: str) -> None:
  from micro.runtime import Runtime
  from micro.service import Service

  async def exercise() -> None:
    async with Runtime(nats_url) as runtime:
      store = Store(Executor())
      await runtime.add(store)
      assert store.engine.active_modules == ()
      people = Service("people")
      people.uses(PEOPLE)
      await runtime.add(people)
      deadline = asyncio.get_running_loop().time() + 10
      while store.engine.active_modules != ("people",):
        assert asyncio.get_running_loop().time() < deadline
        await asyncio.sleep(0.05)
      result = await StoreClient(runtime).execute(
        'query { person(name: "Ada") { name } }'
      )
      assert result == {"data": {"person": {"name": "Ada"}}}

  asyncio.run(exercise())
