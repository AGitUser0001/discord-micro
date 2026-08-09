import asyncio
from typing import Any

import httpx2

from micro.gateway import GatewayEventService


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

  event_service = GatewayEventService(transport=httpx2.MockTransport(respond))
  event_service.apply_state(
    {
      "revision": 0,
      "schemas": {
        "audit-v1": event_schema("audit", "audit:v1"),
        "audit-v2": event_schema("audit", "audit:v2"),
        "metrics-v1": event_schema("metrics", "metrics:v1"),
      },
      "instances": [
        {
          "id": "audit-1",
          "base_url": "http://audit-one.internal",
          "schema": "audit-v1",
        },
        {
          "id": "audit-2",
          "base_url": "http://audit-two.internal",
          "schema": "audit-v2",
        },
        {
          "id": "metrics-1",
          "base_url": "http://metrics.internal",
          "schema": "metrics-v1",
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
      await event_service.queue.aclose()

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

  event_service = GatewayEventService(transport=httpx2.MockTransport(respond))
  event_service.apply_state(
    {
      "revision": 0,
      "schemas": {
        "v1": event_schema("audit", "v1"),
        "v2": event_schema("audit", "v2"),
      },
      "instances": [
        {
          "id": "audit-1",
          "base_url": "http://one.internal",
          "schema": "v1",
        },
        {
          "id": "audit-2",
          "base_url": "http://two.internal",
          "schema": "v2",
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
      await event_service.queue.aclose()

  asyncio.run(exercise())
  assert calls == ["one.internal", "two.internal"]


def test_gateway_event_consumer_drops_poison_and_retries_delivery_failures() -> None:
  deliveries = [b"not a gateway event", b'["MESSAGE_CREATE",{}]']
  settlements: list[str] = []
  finished = asyncio.Event()

  def respond(request: httpx2.Request) -> httpx2.Response:
    if "/consumers/" in request.url.path:
      if deliveries:
        return httpx2.Response(
          200,
          content=deliveries.pop(0),
          headers={"micro-receipt": f"receipt-{len(deliveries)}"},
        )
      return httpx2.Response(503)
    if request.url.path.startswith("/deliveries/"):
      action = request.url.path.rsplit("/", 1)[-1]
      settlements.append(action)
      if len(settlements) == 2:
        finished.set()
      return httpx2.Response(204)
    return httpx2.Response(503)

  event_service = GatewayEventService(transport=httpx2.MockTransport(respond))
  event_service.apply_state(
    {
      "revision": 0,
      "schemas": {"audit": event_schema("audit", "v1")},
      "instances": [
        {
          "id": "audit-1",
          "base_url": "http://audit.internal",
          "schema": "audit",
        }
      ],
      "queues": [{"id": "queue-1", "base_url": "http://queue.internal"}],
    }
  )

  async def exercise() -> None:
    await event_service.start()
    await asyncio.wait_for(finished.wait(), 1)
    await event_service.close()

  asyncio.run(exercise())
  assert settlements == ["acknowledge", "retry"]
