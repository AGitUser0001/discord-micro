import json
from typing import Any, cast
from uuid import uuid4

from graphglot.dialect import Dialect
from psycopg import AsyncConnection, sql
from psycopg_pool import AsyncConnectionPool

from micro.service import JsonValue
from micro.store import GraphResult, GraphStatement


class ApacheAgeExecutor:
  """Execute Micro's canonical GQL against an Apache AGE graph."""

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

    return GraphResult(
      tuple(
        {
          column: _decode_agtype(value)
          for column, value in zip(statement.columns, row, strict=True)
        }
        for row in values
      )
    )

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


__all__ = ("ApacheAgeExecutor",)
