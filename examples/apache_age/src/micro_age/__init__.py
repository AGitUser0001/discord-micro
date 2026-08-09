import hashlib
import json
from typing import Any, LiteralString, cast
from uuid import uuid4

from graphglot.dialect import Dialect
from psycopg import AsyncConnection, Error, sql
from psycopg_pool import AsyncConnectionPool
from pydantic import JsonValue

from micro.store import (
  GraphBackendError,
  GraphBatch,
  GraphBatchResult,
  GraphLayout,
  GraphResult,
  GraphStatement,
)


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

  async def execute(self, batch: GraphBatch) -> GraphBatchResult:
    try:
      async with self._pool.connection() as connection, connection.transaction():
        results = []
        for statement in batch.statements:
          results.append(await self._execute_statement(connection, statement))
      return GraphBatchResult(tuple(results))
    except Error as exc:
      raise _backend_error(exc) from exc

  async def apply_layout(self, layout: GraphLayout) -> None:
    """Create missing labels/indexes; old physical fields remain readable."""
    try:
      async with self._pool.connection() as connection, connection.transaction():
        await connection.execute(
          """
          CREATE TABLE IF NOT EXISTS public.micro_graph_layout (
            revision bigint PRIMARY KEY,
            definition jsonb NOT NULL
          )
          """
        )
        for entity in layout.entities:
          exists = await connection.execute(
            """
            SELECT 1
            FROM ag_catalog.ag_label AS label
            JOIN ag_catalog.ag_graph AS graph ON graph.graphid = label.graph
            WHERE graph.name = %s AND label.name = %s AND label.kind = 'v'
            """,
            (self._graph, entity.label),
          )
          if await exists.fetchone() is None:
            await connection.execute(
              "SELECT ag_catalog.create_vlabel(%s, %s)",
              (self._graph, entity.label),
            )
          index_name = (
            "micro_identity_" + hashlib.sha256(entity.label.encode()).hexdigest()[:20]
          )
          await connection.execute(
            sql.SQL(
              "CREATE UNIQUE INDEX IF NOT EXISTS {} ON {}.{} "
              "(ag_catalog.agtype_access_operator(properties, "
              "'\"_micro_id\"'::ag_catalog.agtype))"
            ).format(
              sql.Identifier(index_name),
              sql.Identifier(self._graph),
              sql.Identifier(entity.label),
            )
          )
        definition = {
          "entities": [
            {
              "name": entity.name,
              "label": entity.label,
              "identity_property": entity.identity_property,
              "keys": entity.keys,
            }
            for entity in layout.entities
          ]
        }
        recorded = await connection.execute(
          """
          INSERT INTO public.micro_graph_layout (revision, definition)
          VALUES (%s, %s::jsonb)
          ON CONFLICT (revision) DO UPDATE
          SET definition = EXCLUDED.definition
          WHERE public.micro_graph_layout.definition = EXCLUDED.definition
          """,
          (layout.revision, json.dumps(definition)),
        )
        if recorded.rowcount == 0:
          raise ValueError(
            f"Graph layout revision {layout.revision} already has another definition."
          )
    except Error as exc:
      raise _backend_error(exc) from exc

  async def _execute_statement(
    self,
    connection: AsyncConnection[Any],
    statement: GraphStatement,
  ) -> GraphResult:
    syntax = self._gql.parse(statement.text)
    if len(syntax) != 1:
      raise ValueError("AGE execution requires exactly one graph statement.")
    cypher = self._cypher.generate(syntax[0])
    # Graphglot preserves ISO GQL's linear-query separator. AGE implements the
    # equivalent openCypher pipeline spelling.
    cypher = cypher.replace(" NEXT ", " WITH * ")
    cypher = cypher.replace(" OFFSET ", " SKIP ")
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
      _dollar_quoted(cypher),
      columns,
    )
    execute = sql.SQL("EXECUTE {} ({})").format(
      sql.Identifier(prepared_name),
      sql.Literal(json.dumps(dict(statement.parameters))),
    )

    prepared = False
    try:
      await connection.execute(prepare)
      prepared = True
      cursor = await connection.execute(execute)
      values = await cursor.fetchall()
    except BaseException:
      if prepared:
        try:
          await connection.execute(
            sql.SQL("DEALLOCATE {}").format(sql.Identifier(prepared_name))
          )
        except Error:
          pass
      raise
    else:
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


def _dollar_quoted(value: str) -> sql.SQL:
  tag = "micro"
  while f"${tag}$" in value:
    tag += "_"
  delimiter = f"${tag}$"
  quoted = cast(LiteralString, f"{delimiter}{value}{delimiter}")
  return sql.SQL(quoted)


def _backend_error(exc: Error) -> GraphBackendError:
  state = exc.sqlstate or ""
  if state == "23505":
    return GraphBackendError(
      "The graph operation conflicts with existing data.", code="CONFLICT"
    )
  if state.startswith(("08", "53", "57")):
    return GraphBackendError(
      "The graph backend is unavailable.", code="UNAVAILABLE", retryable=True
    )
  if state.startswith(("22", "23", "42")):
    return GraphBackendError("The graph operation was rejected.", code="INVALID")
  return GraphBackendError("The graph backend failed.", code="INTERNAL")


__all__ = ("ApacheAgeExecutor",)
