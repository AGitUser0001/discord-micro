import asyncio
from typing import Any

import httpx2

from micro.gateway import GatewayEventService


class Source:
  async def start(self) -> None:
    pass

  async def receive(self) -> Any:
    raise AssertionError("The unit test calls route directly.")

  async def close(self) -> None:
    pass


def event_schema(service: str, handler: str) -> dict[str, Any]:
  return {
    "format": 1,
    "kind": "service",
    "service": service,
    "asgi": {},
    "implementation_hash": f"sha256:{handler}",
    "events": [
      {
        "id": "MESSAGE_CREATE",
        "path": "/events/MESSAGE_CREATE",
        "payload": {"type": "object"},
        "handler": handler,
      }
    ],
    "requests": [],
  }


def test_gateway_event_service_delivers_once_per_service_name() -> None:
  calls: list[tuple[str, bytes]] = []

  def respond(request: httpx2.Request) -> httpx2.Response:
    calls.append((request.url.host, request.read()))
    return httpx2.Response(204)

  event_service = GatewayEventService(
    source=Source(),
    transport=httpx2.MockTransport(respond),
  )
  event_service.apply_state(
    {
      "revision": 0,
      "instances": [
        {
          "id": "audit-1",
          "base_url": "http://audit-one.internal",
          "schema": event_schema("audit", "audit:v1"),
        },
        {
          "id": "audit-2",
          "base_url": "http://audit-two.internal",
          "schema": event_schema("audit", "audit:v2"),
        },
        {
          "id": "metrics-1",
          "base_url": "http://metrics.internal",
          "schema": event_schema("metrics", "metrics:v1"),
        },
      ],
    }
  )

  async def exercise() -> int:
    try:
      return await event_service.route(
        b'["MESSAGE_CREATE",{"id":"1","content":"hello"}]'
      )
    finally:
      await event_service.client.aclose()

  assert asyncio.run(exercise()) == 2
  assert calls == [
    ("audit-one.internal", b'{"id":"1","content":"hello"}'),
    ("metrics.internal", b'{"id":"1","content":"hello"}'),
  ]


def test_gateway_event_service_round_robins_replicas_without_hash_grouping() -> None:
  calls: list[str] = []

  def respond(request: httpx2.Request) -> httpx2.Response:
    calls.append(request.url.host)
    return httpx2.Response(204)

  event_service = GatewayEventService(
    source=Source(), transport=httpx2.MockTransport(respond)
  )
  event_service.apply_state(
    {
      "revision": 0,
      "instances": [
        {
          "id": "audit-1",
          "base_url": "http://one.internal",
          "schema": event_schema("audit", "v1"),
        },
        {
          "id": "audit-2",
          "base_url": "http://two.internal",
          "schema": event_schema("audit", "v2"),
        },
      ],
    }
  )

  async def exercise() -> None:
    try:
      await event_service.route(b'["MESSAGE_CREATE",{}]')
      await event_service.route(b'["MESSAGE_CREATE",{}]')
    finally:
      await event_service.client.aclose()

  asyncio.run(exercise())
  assert calls == ["one.internal", "two.internal"]
