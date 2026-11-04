"""A store backed by Apache AGE: `uv run micro run store:store micro.http:HTTPBridge`."""

import os

from micro_age import ApacheAgeExecutor

from micro.store import GraphModule, Store

PEOPLE = GraphModule(
  id="example.people",
  schema="""
    type Person @entity(key: ["name"]) { name: String! }
    type Query { person(name: String!): Person @from(key: {name: name}) }
    type Mutation {
      createPerson(name: String!): Person!
        @insert(key: {name: name}, set: {name: name})
    }
  """,
)

store = Store(
  ApacheAgeExecutor(
    os.environ.get("MICRO_AGE_URL", "postgresql://micro:micro@127.0.0.1:5455/micro")
  ),
  modules=[PEOPLE],
)
