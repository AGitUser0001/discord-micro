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


class Delivery:
  def __init__(self, payload: bytes) -> None:
    self.payload = payload
    self.acknowledged = asyncio.Event()
    self.retried = asyncio.Event()

  async def acknowledge(self) -> None:
    self.acknowledged.set()

  async def retry(self) -> None:
    self.retried.set()


class LiveSource:
  def __init__(self) -> None:
    self.items: asyncio.Queue[Delivery] = asyncio.Queue()

  async def start(self) -> None:
    pass

  async def receive(self) -> Delivery:
    return await self.items.get()

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

  asyncio.run(exercise())
  assert calls == ["one.internal", "two.internal"]


def test_gateway_event_consumer_drops_poison_and_retries_delivery_failures() -> None:
  source = LiveSource()

  def respond(request: httpx2.Request) -> httpx2.Response:
    return httpx2.Response(503)

  event_service = GatewayEventService(
    source=source,
    transport=httpx2.MockTransport(respond),
  )
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
    }
  )
  poison = Delivery(b"not a gateway event")
  transient = Delivery(b'["MESSAGE_CREATE",{}]')

  async def exercise() -> None:
    await event_service.start()
    await source.items.put(poison)
    await asyncio.wait_for(poison.acknowledged.wait(), 1)
    await source.items.put(transient)
    await asyncio.wait_for(transient.retried.wait(), 1)
    await event_service.close()

  asyncio.run(exercise())
  assert not poison.retried.is_set()
  assert not transient.acknowledged.is_set()
