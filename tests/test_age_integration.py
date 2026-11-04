import os
from typing import Any
from uuid import uuid4

import pytest
from conftest import EngineHarness

from micro.schemas.gateway import GATEWAY_PROJECTION

ApacheAgeExecutor: Any = pytest.importorskip("micro_age").ApacheAgeExecutor

AGE_URL = os.getenv("MICRO_AGE_TEST_URL")
pytestmark = pytest.mark.skipif(
  AGE_URL is None,
  reason="Set MICRO_AGE_TEST_URL to run Apache AGE integration tests.",
)


def test_age_executes_projection_writes_relationships_deletes_and_rollbacks() -> None:
  assert AGE_URL is not None
  suffix = uuid4().hex
  connection_id = f"connection-{suffix}"
  object_id = f"guild-{suffix}"
  rollback_id = f"rollback-{suffix}"
  store = EngineHarness(ApacheAgeExecutor(AGE_URL))

  with store as client:
    topology = client.post(
      "/topology",
      json={
        "revision": int(suffix[:12], 16),
        "modules": [GATEWAY_PROJECTION.model_dump(by_alias=True)],
      },
    )
    assert topology.status_code == 204
    ready = client.post(
      "/graphql",
      json={
        "query": """
          mutation Ready($id: ID!) {
            createGatewayConnection(
              id: $id, shardId: 0, active: true, state: "ready"
            ) { id }
          }
        """,
        "variables": {"id": connection_id},
      },
    )
    assert ready.json().get("errors") is None
    created = client.post(
      "/graphql",
      json={
        "query": """
          mutation Create($connection: ID!, $id: ID!, $payload: JSON!) {
            createDiscordObject(
              connectionId: $connection, kind: "guild", id: $id,
              payload: $payload
            ) { id }
            attachDiscordObject(
              connectionId: $connection, kind: "guild", id: $id
            )
          }
        """,
        "variables": {
          "connection": connection_id,
          "id": object_id,
          "payload": {"id": object_id, "name": "one"},
        },
      },
    )
    assert created.json().get("errors") is None
    read = client.post(
      "/graphql",
      json={
        "query": "query Read($id: ID!) { gatewayConnection(id: $id) { data { id } } }",
        "variables": {"id": connection_id},
      },
    )
    assert read.json()["data"]["gatewayConnection"]["data"] == [{"id": object_id}]
    page = client.post(
      "/graphql",
      json={"query": "{ projectionDiscordObjects(first: 1, offset: 0) { id } }"},
    )
    assert page.json().get("errors") is None, page.json()
    assert len(page.json()["data"]["projectionDiscordObjects"]) == 1
    stale = client.post(
      "/graphql",
      json={
        "query": """
          mutation Stale($id: ID!) {
            updateGatewayConnection(id: $id, active: false, state: "disconnected") { id }
          }
        """,
        "variables": {"id": connection_id},
      },
    )
    assert stale.json().get("errors") is None
    hidden = client.post(
      "/graphql",
      json={
        "query": """
          query Cached($connection: ID!, $id: ID!) {
            discordObject(connectionId: $connection, kind: "guild", id: $id) { id }
          }
        """,
        "variables": {"connection": connection_id, "id": object_id},
      },
    )
    assert hidden.json()["data"]["discordObject"] is None
    resumed = client.post(
      "/graphql",
      json={
        "query": """
          mutation Resume($id: ID!) {
            updateGatewayConnection(id: $id, active: true, state: "resumed") { id }
          }
        """,
        "variables": {"id": connection_id},
      },
    )
    assert resumed.json().get("errors") is None

    rolled_back = client.post(
      "/graphql",
      json={
        "query": """
          mutation Conflict($connection: ID!, $id: ID!, $payload: JSON!) {
            first: createDiscordObject(
              connectionId: $connection, kind: "guild", id: $id,
              payload: $payload
            ) { id }
            second: createDiscordObject(
              connectionId: $connection, kind: "guild", id: $id,
              payload: $payload
            ) { id }
          }
        """,
        "variables": {
          "connection": connection_id,
          "id": rollback_id,
          "payload": {"id": rollback_id},
        },
      },
    )
    assert rolled_back.json()["errors"][0]["extensions"]["code"] == "CONFLICT"
    absent = client.post(
      "/graphql",
      json={
        "query": """
          query Read($connection: ID!, $id: ID!) {
            discordObject(connectionId: $connection, kind: "guild", id: $id) { id }
          }
        """,
        "variables": {"connection": connection_id, "id": rollback_id},
      },
    )
    assert absent.json()["data"]["discordObject"] is None

    deleted = client.post(
      "/graphql",
      json={
        "query": """
          mutation Delete($connection: ID!, $id: ID!) {
            deleteDiscordObject(connectionId: $connection, kind: "guild", id: $id)
          }
        """,
        "variables": {"connection": connection_id, "id": object_id},
      },
    )
    assert deleted.json().get("errors") is None
