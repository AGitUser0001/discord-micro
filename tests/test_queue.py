import asyncio

import httpx2
import pytest
from starlette.testclient import TestClient

from micro._microservices import NoCompatibleInstanceError
from micro.queue import Queue, QueueClient


class Backend:
  def __init__(self) -> None:
    self.started = False
    self.closed = False
    self.items: list[tuple[str, bytes]] = []

  async def start(self) -> None:
    self.started = True

  async def publish(self, channel: str, payload: bytes) -> None:
    self.items.append((channel, payload))

  async def close(self) -> None:
    self.closed = True


def test_queue_publishes_raw_items_to_its_backend() -> None:
  backend = Backend()
  queue = Queue(backend=backend)

  with TestClient(queue) as client:
    response = client.post(
      "/channels/gateway.events",
      content=b"\x00payload\xff",
      headers={"content-type": "application/octet-stream"},
    )

  assert response.status_code == 204
  assert backend.items == [("gateway.events", b"\x00payload\xff")]
  assert backend.started
  assert backend.closed


def test_queue_rejects_invalid_channels() -> None:
  with TestClient(Queue(backend=Backend())) as client:
    response = client.post("/channels/bad%20channel", content=b"payload")

  assert response.status_code == 422


def test_queue_client_routes_raw_items_across_instances() -> None:
  calls: list[tuple[str, str, bytes, str | None]] = []

  def respond(request: httpx2.Request) -> httpx2.Response:
    calls.append(
      (
        request.url.host,
        request.url.path,
        request.read(),
        request.headers.get("content-type"),
      )
    )
    return httpx2.Response(204)

  async def exercise() -> None:
    async with QueueClient(transport=httpx2.MockTransport(respond)) as client:
      client.apply_state(
        {
          "revision": 0,
          "queues": [
            {"id": "queue-1", "base_url": "http://one.internal"},
            {"id": "queue-2", "base_url": "http://two.internal"},
          ],
        }
      )
      await client.publish("gateway.events", b"one")
      await client.publish("gateway.events", b"two")

  asyncio.run(exercise())
  assert calls == [
    (
      "one.internal",
      "/channels/gateway.events",
      b"one",
      "application/octet-stream",
    ),
    (
      "two.internal",
      "/channels/gateway.events",
      b"two",
      "application/octet-stream",
    ),
  ]


def test_queue_client_requires_a_discovered_queue() -> None:
  async def exercise() -> None:
    async with QueueClient() as client:
      with pytest.raises(NoCompatibleInstanceError):
        await client.publish("events", b"payload")

  asyncio.run(exercise())
