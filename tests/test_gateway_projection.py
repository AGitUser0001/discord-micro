import asyncio
from collections.abc import Mapping
from typing import Any

from pydantic import JsonValue

from micro.gateway import ConnectionEvent, ConnectionEventKind
from micro.gateway.projection import GatewayProjection
from micro.schemas.gateway import GATEWAY_PROJECTION
from micro.store import compose_graph


def event(kind: ConnectionEventKind) -> ConnectionEvent:
  return ConnectionEvent(
    kind=kind, shard_id=0, generation=1, connection_id="connection-a", worker="w"
  )


def test_gateway_projection_schema_is_composable() -> None:
  graph = compose_graph((GATEWAY_PROJECTION,))

  assert set(graph.entities) == {"GatewayConnection", "DiscordObject"}
  assert ("Mutation", "createDiscordObject") in graph.bindings
  assert ("Mutation", "updateDiscordObject") in graph.bindings


def test_gateway_projection_fuses_partial_updates() -> None:
  projection = GatewayProjection()
  calls: list[tuple[str, Mapping[str, JsonValue]]] = []

  async def execute(query: str, variables: Mapping[str, JsonValue]) -> dict[str, Any]:
    calls.append((query, variables))
    if "query Existing" in query:
      return {
        "object0": {
          "payload": {
            "id": "10",
            "author": {"id": "20", "username": "before"},
            "content": "old",
          }
        }
      }
    return {"updateDiscordObject": {"id": "10"}}

  projection._execute = execute  # type: ignore[method-assign]

  async def exercise() -> None:
    try:
      await projection.project_events(
        [
          (
            "connection-a",
            "MESSAGE_UPDATE",
            {"id": "10", "author": {"username": "after"}, "content": "new"},
          )
        ]
      )
    finally:
      await projection.close()

  asyncio.run(exercise())

  mutation = calls[-1]
  assert "updateDiscordObject" in mutation[0]
  assert mutation[1]["payload0"] == {
    "id": "10",
    "author": {"id": "20", "username": "after"},
    "content": "new",
  }


def test_gateway_projection_ingests_guild_collections_deterministically() -> None:
  projection = GatewayProjection()
  created: list[tuple[str, str]] = []

  async def execute(query: str, variables: Mapping[str, JsonValue]) -> dict[str, Any]:
    if "query Existing" in query:
      return {f"object{index}": None for index in range(4)}
    if "createDiscordObject" in query:
      created.extend(
        (str(variables[f"kind{index}"]), str(variables[f"id{index}"]))
        for index in range(4)
      )
      return {f"write{index}": {"id": variables[f"id{index}"]} for index in range(4)}
    return {}

  projection._execute = execute  # type: ignore[method-assign]

  async def exercise() -> None:
    try:
      await projection.project_events(
        [
          (
            "connection-a",
            "GUILD_CREATE",
            {
              "id": "1",
              "channels": [{"id": "2"}],
              "roles": [{"id": "3"}],
              "members": [{"user": {"id": "4"}}],
            },
          )
        ]
      )
    finally:
      await projection.close()

  asyncio.run(exercise())
  assert created == [
    ("guild", "1"),
    ("channel", "2"),
    ("role", "3"),
    ("member", "4"),
  ]


def test_projection_connection_state_goes_stale_resumes_and_purges_atomically() -> None:
  projection = GatewayProjection()
  calls: list[tuple[str, Mapping[str, JsonValue]]] = []

  async def execute(query: str, variables: Mapping[str, JsonValue]) -> dict[str, Any]:
    calls.append((query, variables))
    if "query Connection" in query:
      return {"gatewayConnection": None}
    if "query Owned" in query:
      return {
        "gatewayConnection": {
          "data": [
            {"connectionId": "connection-a", "kind": "guild", "id": "1"},
            {"connectionId": "connection-a", "kind": "channel", "id": "2"},
          ]
        }
      }
    return {"ok": True}

  projection._execute = execute  # type: ignore[method-assign]

  async def exercise() -> None:
    try:
      await projection.project_connection(event(ConnectionEventKind.READY))
      await projection.project_connection(event(ConnectionEventKind.DISCONNECTED))
      await projection.project_connection(event(ConnectionEventKind.RESUMED))
      await projection.project_connection(event(ConnectionEventKind.INVALIDATED))
    finally:
      await projection.close()

  asyncio.run(exercise())

  state_calls = [call for call in calls if "updateGatewayConnection" in call[0]]
  assert state_calls[0][1]["active"] is False
  assert state_calls[1][1]["active"] is True
  purge = calls[-1]
  assert purge[0].count("deleteDiscordObject") == 2
  assert purge[0].count("deleteGatewayConnection") == 1
  assert purge[1]["connectionId"] == "connection-a"


def test_projection_batch_replay_is_deterministic() -> None:
  projection = GatewayProjection()
  stored: dict[str, JsonValue] | None = None
  writes = 0

  async def execute(query: str, variables: Mapping[str, JsonValue]) -> dict[str, Any]:
    nonlocal stored, writes
    if "query Existing" in query:
      return {"object0": {"payload": stored} if stored is not None else None}
    writes += 1
    payload = variables["payload0"]
    assert isinstance(payload, dict)
    stored = dict(payload)
    return {"write0": {"id": "10"}}

  projection._execute = execute  # type: ignore[method-assign]
  events: list[tuple[str, str, dict[str, JsonValue]]] = [
    (
      "connection-a",
      "MESSAGE_CREATE",
      {"id": "10", "author": {"id": "20"}, "content": "one"},
    ),
    ("connection-a", "MESSAGE_UPDATE", {"id": "10", "content": "two"}),
  ]

  async def exercise() -> None:
    try:
      await projection.project_events(events)
      first = dict(stored or {})
      await projection.project_events(events)
      assert stored == first
    finally:
      await projection.close()

  asyncio.run(exercise())

  assert writes == 2
  assert stored == {
    "id": "10",
    "author": {"id": "20"},
    "content": "two",
  }
