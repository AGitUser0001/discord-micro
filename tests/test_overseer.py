import asyncio
from typing import Any

import httpx2
from starlette.testclient import TestClient

from micro.overseer import DiscoveredInstance, NetworkDiscovery, Overseer, StoreModule

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
    ]
  )

  async def exercise() -> Overseer:
    overseer = Overseer(
      discovery,
      transport=httpx2.MockTransport(respond),
      modules=(
        StoreModule(
          id="guilds",
          schema="extend type Query { guild(id: ID!): String }",
        ),
        StoreModule(
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
  assert service_request[:2] == ("service.internal", "/state")
  assert '"revision":0' in service_request[2].replace(" ", "")
  assert store_request[:2] == ("store.internal", "/topology")
  assert '"id":"guilds"' in store_request[2].replace(" ", "")
  assert '"id":"members"' in store_request[2].replace(" ", "")
  assert overseer.revision == 0
