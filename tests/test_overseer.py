import asyncio
import json
from typing import Any

import httpx2
import pytest
from starlette.testclient import TestClient

from micro.gateway import ConnectionEvent, ConnectionEventKind
from micro.overseer import (
  DiscoveredInstance,
  GraphModule,
  MemoryOverseerPersistence,
  NetworkDiscovery,
  Overseer,
  TopologyPushError,
)

SERVICE_SCHEMA: dict[str, Any] = {
  "format": 1,
  "service": "example",
  "asgi": {},
  "events": [],
  "requests": [],
}


def test_network_discovery_has_asgi_control_surface() -> None:
  discovery = NetworkDiscovery()

  with TestClient(discovery) as client:
    added = client.post(
      "/instances",
      json={
        "id": "store-1",
        "base_url": "http://store.internal",
        "role": "store",
        "modules": ["guilds"],
      },
    )
    instances = client.get("/instances")
    removed = client.delete("/instances/store-1")

  assert added.status_code == 204
  assert instances.json()[0]["modules"] == ["guilds"]
  assert removed.status_code == 204
  assert asyncio.run(discovery.snapshot()) == ()


def test_overseer_pushes_discovered_topology() -> None:
  requests: list[tuple[str, str, str]] = []

  def respond(request: httpx2.Request) -> httpx2.Response:
    requests.append((request.url.host, request.url.path, request.read().decode()))
    return httpx2.Response(204)

  discovery = NetworkDiscovery(
    [
      DiscoveredInstance(
        id="service-1",
        base_url="http://service.internal",
        role="service",
        schema=SERVICE_SCHEMA,
      ),
      DiscoveredInstance(
        id="store-1",
        base_url="http://store.internal",
        role="store",
        modules=("guilds", "members"),
      ),
      DiscoveredInstance(
        id="queue-1",
        base_url="http://queue.internal",
        role="queue",
      ),
      DiscoveredInstance(
        id="gateway-events-1",
        base_url="http://gateway-events.internal",
        role="gateway.event_service",
      ),
    ]
  )

  async def exercise() -> Overseer:
    overseer = Overseer(
      discovery,
      transport=httpx2.MockTransport(respond),
      modules=(
        GraphModule(
          id="guilds",
          schema="extend type Query { guild(id: ID!): String }",
        ),
        GraphModule(
          id="members",
          schema="extend type Query { member(id: ID!): String }",
        ),
      ),
    )
    assert await overseer.reconcile() == 0
    await overseer.aclose()
    return overseer

  overseer = asyncio.run(exercise())
  service_request = requests[0]
  store_request = requests[1]
  gateway_event_request = requests[2]
  assert service_request[:2] == ("service.internal", "/state")
  assert '"revision":0' in service_request[2].replace(" ", "")
  assert '"base_url":"http://store.internal"' in service_request[2].replace(" ", "")
  assert '"base_url":"http://queue.internal"' in service_request[2].replace(" ", "")
  assert store_request[:2] == ("store.internal", "/topology")
  assert '"id":"guilds"' in store_request[2].replace(" ", "")
  assert '"id":"members"' in store_request[2].replace(" ", "")
  assert gateway_event_request[:2] == ("gateway-events.internal", "/state")
  assert overseer.revision == 0


def test_overseer_composes_each_store_assignment_independently() -> None:
  discovery = NetworkDiscovery(
    (
      DiscoveredInstance(
        id="guild-store",
        base_url="http://guild-store.internal",
        role="store",
        modules=("guilds",),
      ),
      DiscoveredInstance(
        id="audit-store",
        base_url="http://audit-store.internal",
        role="store",
        modules=("audit",),
      ),
    )
  )
  modules = (
    GraphModule(id="guilds", schema="type Query { item: String }"),
    GraphModule(id="audit", schema="type Query { item: Int }"),
  )

  async def exercise() -> Overseer:
    overseer = Overseer(
      discovery,
      modules=modules,
      transport=httpx2.MockTransport(lambda request: httpx2.Response(204)),
    )
    await overseer.reconcile()
    await overseer.aclose()
    return overseer

  overseer = asyncio.run(exercise())

  assert set(overseer.store_graphs) == {"guild-store", "audit-store"}
  assert overseer.store_graphs["guild-store"].modules == ("guilds",)
  assert overseer.store_graphs["audit-store"].modules == ("audit",)


def test_overseer_loads_replaces_and_unloads_graph_modules() -> None:
  overseer = Overseer(NetworkDiscovery())
  valid = GraphModule(
    id="guilds",
    schema="""
      type Guild @entity(key: ["id"]) { id: ID! }
      type Query {
        guild(id: ID!): Guild @from(key: {id: id})
      }
    """,
  )
  invalid_replacement = GraphModule(
    id="guilds",
    schema="""
      type Guild @entity(key: ["id"]) { id: ID! }
      type Query { guild(id: ID!): Guild }
    """,
  )

  overseer.load_graph_module(valid)
  assert overseer.graph_modules == (valid,)

  overseer.load_graph_module(invalid_replacement)
  assert overseer.graph_modules == (invalid_replacement,)

  assert overseer.unload_graph_module("guilds")
  assert overseer.graph_modules == ()
  assert not overseer.unload_graph_module("guilds")


def test_failed_push_does_not_reuse_its_revision() -> None:
  pushed_revisions: list[int] = []
  fail = True

  def respond(request: httpx2.Request) -> httpx2.Response:
    nonlocal fail
    revision = json.loads(request.read())["revision"]
    pushed_revisions.append(revision)
    if fail:
      fail = False
      return httpx2.Response(503)
    return httpx2.Response(204)

  discovery = NetworkDiscovery(
    (
      DiscoveredInstance(
        id="service-1",
        base_url="http://service.internal",
        role="service",
        schema=SERVICE_SCHEMA,
      ),
    )
  )

  async def exercise() -> Overseer:
    overseer = Overseer(discovery, transport=httpx2.MockTransport(respond))
    try:
      with pytest.raises(TopologyPushError):
        await overseer.reconcile()
      assert await overseer.reconcile() == 1
      return overseer
    finally:
      await overseer.aclose()

  overseer = asyncio.run(exercise())
  assert pushed_revisions == [0, 1]
  assert overseer.revision == 1


def test_overseer_separates_desired_assignments_from_observed_connections() -> None:
  paths: list[str] = []

  def respond(request: httpx2.Request) -> httpx2.Response:
    paths.append(request.url.path)
    return httpx2.Response(204)

  discovery = NetworkDiscovery(
    (
      DiscoveredInstance(
        id="gateway-a",
        base_url="http://gateway.internal",
        role="gateway",
        shard_ids=(0,),
        shard_count=1,
      ),
      DiscoveredInstance(
        id="projection-a",
        base_url="http://projection.internal",
        role="gateway.projection",
      ),
    )
  )

  async def exercise() -> Overseer:
    overseer = Overseer(
      discovery,
      transport=httpx2.MockTransport(respond),
    )
    await overseer.reconcile()
    assert overseer.gateway_state.active_shards("gateway-a") == ()
    overseer.observe_gateway_connection(
      "gateway-a",
      ConnectionEvent(ConnectionEventKind.READY, 0, "connection-a"),
    )
    assert overseer.gateway_state.active_shards("gateway-a") == (0,)
    assert await overseer.declare_gateway_dead("gateway-a") == ("connection-a",)
    await overseer.aclose()
    return overseer

  overseer = asyncio.run(exercise())
  assert overseer.gateway_state.active_shards("gateway-a") == ()
  assert "/projection/connections/connection-a" in paths


def test_overseer_persists_reserved_revisions_across_restart() -> None:
  persistence = MemoryOverseerPersistence()
  discovery = NetworkDiscovery(
    (
      DiscoveredInstance(
        id="service-1",
        base_url="http://service.internal",
        role="service",
        schema=SERVICE_SCHEMA,
      ),
    )
  )

  async def exercise() -> tuple[int, int]:
    first = Overseer(
      discovery,
      persistence=persistence,
      transport=httpx2.MockTransport(lambda request: httpx2.Response(503)),
    )
    with pytest.raises(TopologyPushError):
      await first.reconcile()
    await first.aclose()
    second = Overseer(
      discovery,
      persistence=persistence,
      transport=httpx2.MockTransport(lambda request: httpx2.Response(204)),
    )
    revision = await second.reconcile()
    next_revision = (
      second.last_reconciliation.revision if second.last_reconciliation else -1
    )
    await second.aclose()
    return revision, next_revision

  assert asyncio.run(exercise()) == (1, 1)


def test_overseer_records_partial_distribution_failures() -> None:
  discovery = NetworkDiscovery(
    (
      DiscoveredInstance(
        id="good",
        base_url="http://good.internal",
        role="service",
        schema=SERVICE_SCHEMA,
      ),
      DiscoveredInstance(
        id="bad",
        base_url="http://bad.internal",
        role="service",
        schema=SERVICE_SCHEMA,
      ),
    )
  )

  def respond(request: httpx2.Request) -> httpx2.Response:
    return httpx2.Response(503 if request.url.host == "bad.internal" else 204)

  async def exercise() -> Overseer:
    overseer = Overseer(discovery, transport=httpx2.MockTransport(respond))
    with pytest.raises(TopologyPushError):
      await overseer.reconcile()
    await overseer.aclose()
    return overseer

  overseer = asyncio.run(exercise())
  assert overseer.distributed_revisions == {"good": 0}
  assert overseer.last_reconciliation is not None
  assert overseer.last_reconciliation.failures[0][0] == "bad"
