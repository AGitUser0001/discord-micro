from __future__ import annotations

import json
import os
from collections.abc import Mapping
from typing import Any, cast
from uuid import uuid4

from graphglot.dialect import Dialect
from graphql import FieldNode, GraphQLError, get_argument_values
from psycopg import AsyncConnection, sql
from psycopg_pool import AsyncConnectionPool

from micro.service import JsonValue
from micro.store import (
  CompiledOperation,
  GraphQLRequest,
  GraphResult,
  GraphStatement,
  Store,
)

SCHEMA = """
  type Person {
    name: String!
  }

  type Query {
    person(name: String!): Person
  }

  type Mutation {
    createPerson(name: String!): Person!
  }
"""


class ExampleCompiler:
  """The application-owned mapping from its GraphQL schema to canonical GQL."""

  def compile(self, request: GraphQLRequest) -> CompiledOperation:
    selections = request.operation.selection_set.selections
    if len(selections) != 1 or not isinstance(selections[0], FieldNode):
      raise GraphQLError("This example accepts one root field per operation.")
    field = selections[0]
    root = request.schema.get_root_type(request.operation.operation)
    if root is None or field.name.value not in root.fields:
      raise GraphQLError("The selected root field is unavailable.")
    arguments = get_argument_values(
      root.fields[field.name.value], field, dict(request.variables)
    )
    name = cast(str, arguments["name"])

    if field.name.value == "person":
      text = (
        "MATCH (person:Person) WHERE person.name = $name RETURN person.name AS name"
      )
      nullable = True
    elif field.name.value == "createPerson":
      text = "INSERT (:Person {name: $name}) RETURN $name AS name"
      nullable = False
    else:
      raise GraphQLError("The selected root field has no graph mapping.")

    statement = GraphStatement(text, {"name": name}, ("name",))

    def shape(result: GraphResult) -> Mapping[str, JsonValue]:
      person: JsonValue
      if result.rows:
        person = dict(result.rows[0])
      elif nullable:
        person = None
      else:
        raise GraphQLError("The mutation did not return its created person.")
      return {field.alias.value if field.alias else field.name.value: person}

    return CompiledOperation(statement, shape)


class ApacheAgeExecutor:
  """Application-side AGE implementation of Micro's graph executor protocol."""

  def __init__(self, connection_info: str, *, graph: str = "micro") -> None:
    self._graph = graph
    self._pool = AsyncConnectionPool(
      connection_info,
      open=False,
      configure=self._configure,
    )
    self._gql = Dialect.get_or_raise("fullgql")
    self._cypher = Dialect.get_or_raise("neo4j")

  async def start(self) -> None:
    await self._pool.open()
    await self._pool.wait()

  async def close(self) -> None:
    await self._pool.close()

  async def execute(self, statement: GraphStatement) -> GraphResult:
    syntax = self._gql.parse(statement.text)
    if len(syntax) != 1:
      raise ValueError("AGE execution requires exactly one graph statement.")
    cypher = self._cypher.generate(syntax[0])
    prepared_name = f"micro_{uuid4().hex}"
    columns = sql.SQL(", ").join(
      sql.SQL("{} agtype").format(sql.Identifier(column))
      for column in statement.columns
    )
    prepare = sql.SQL(
      "PREPARE {}(agtype) AS SELECT * FROM cypher({}, {}, $1) AS ({})"
    ).format(
      sql.Identifier(prepared_name),
      sql.Literal(self._graph),
      sql.Literal(cypher),
      columns,
    )
    execute = sql.SQL("EXECUTE {} ({})").format(
      sql.Identifier(prepared_name),
      sql.Literal(json.dumps(dict(statement.parameters))),
    )

    async with self._pool.connection() as connection:
      prepared = False
      try:
        async with connection.transaction():
          await connection.execute(prepare)
          prepared = True
          cursor = await connection.execute(execute)
          values = await cursor.fetchall()
      finally:
        if prepared:
          await connection.execute(
            sql.SQL("DEALLOCATE {}").format(sql.Identifier(prepared_name))
          )

    rows = tuple(
      {
        column: _decode_agtype(value)
        for column, value in zip(statement.columns, row, strict=True)
      }
      for row in values
    )
    return GraphResult(rows)

  @staticmethod
  async def _configure(connection: AsyncConnection[Any]) -> None:
    await connection.execute("LOAD 'age'")
    await connection.execute('SET search_path = ag_catalog, "$user", public')
    await connection.commit()


def _decode_agtype(value: Any) -> JsonValue:
  if value is None or isinstance(value, bool | int | float | list | dict):
    return cast(JsonValue, value)
  if not isinstance(value, str):
    raise TypeError(f"Unsupported agtype result {type(value).__name__}.")
  try:
    return cast(JsonValue, json.loads(value))
  except json.JSONDecodeError:
    return value


executor = ApacheAgeExecutor(
  os.environ.get(
    "MICRO_AGE_URL",
    "postgresql://micro:micro@127.0.0.1:5455/micro",
  )
)
store = Store(SCHEMA, compiler=ExampleCompiler(), executor=executor)
