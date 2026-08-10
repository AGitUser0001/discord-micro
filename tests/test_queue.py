import asyncio

import httpx2
import pytest
from starlette.testclient import TestClient

from micro._microservices import NoCompatibleInstanceError, OperationEvent
from micro.queue import Queue, QueueBackendDelivery, QueueClient, QueueObservation


class Backend:
  def __init__(self) -> None:
    self.started = False
    self.closed = False
    self.items: list[tuple[str, bytes]] = []
    self.requests: list[tuple[str, bytes, float]] = []
    self.deliveries: asyncio.Queue[QueueBackendDelivery] = asyncio.Queue()
    self.settlements: list[tuple[str, str, str | None, bytes]] = []

  async def start(self) -> None:
    self.started = True

  async def publish(self, channel: str, payload: bytes) -> None:
    self.items.append((channel, payload))

  async def request(self, channel: str, payload: bytes, *, timeout: float) -> bytes:
    self.requests.append((channel, payload, timeout))
    return b"response"

  async def consume(
    self, channel: str, consumer: str, *, timeout: float
  ) -> QueueBackendDelivery | None:
    return await self.deliveries.get()

  async def acknowledge(self, receipt: str) -> None:
    self.settlements.append(("acknowledge", receipt, None, b""))

  async def retry(self, receipt: str, *, delay: float = 0) -> None:
    self.settlements.append(("retry", receipt, None, b""))

  async def dead_letter(self, receipt: str) -> None:
    self.settlements.append(("dead_letter", receipt, None, b""))

  async def respond(self, receipt: str, reply: str, payload: bytes) -> None:
    self.settlements.append(("respond", receipt, reply, payload))

  async def close(self) -> None:
    self.closed = True

  async def observe(self) -> QueueObservation:
    return QueueObservation(True, pending=self.deliveries.qsize(), consumers=1)


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


def test_queue_emits_structured_operation_events() -> None:
  backend = Backend()
  queue = Queue(backend=backend)
  events: list[OperationEvent] = []

  async def observe(event: OperationEvent) -> None:
    events.append(event)

  queue.add_operation_observer(observe)
  with TestClient(queue) as client:
    assert client.post("/channels/events", content=b"payload").status_code == 204

  assert [(event.operation, event.phase) for event in events] == [
    ("publish", "started"),
    ("publish", "completed"),
  ]


def test_queue_rejects_invalid_channels() -> None:
  with TestClient(Queue(backend=Backend())) as client:
    response = client.post("/channels/bad%20channel", content=b"payload")

  assert response.status_code == 422


def test_queue_enforces_size_limits_and_exposes_observations() -> None:
  backend = Backend()
  with TestClient(Queue(backend=backend, max_payload_size=4)) as client:
    oversized = client.post("/channels/jobs", content=b"12345")
    observed = client.get("/queue/observations")

  assert oversized.status_code == 413
  assert observed.json() == {
    "connected": True,
    "pending": 0,
    "consumers": 1,
    "active_operations": 0,
    "accepting": True,
  }


def test_queue_supports_delayed_retry_and_dead_letter_policy() -> None:
  backend = Backend()
  backend.deliveries.put_nowait(QueueBackendDelivery(b"job", "receipt"))
  with TestClient(Queue(backend=backend)) as client:
    consumed = client.post("/channels/jobs/consumers/worker")
    headers = {"micro-receipt": consumed.headers["micro-receipt"]}
    retried = client.post("/deliveries/retry?delay=2", headers=headers)
    dead = client.post("/deliveries/dead_letter", headers=headers)

  assert retried.status_code == dead.status_code == 204
  assert backend.settlements == [
    ("retry", "receipt", None, b""),
    ("dead_letter", "receipt", None, b""),
  ]


def test_queue_serves_request_and_delivery_settlement() -> None:
  backend = Backend()
  backend.deliveries.put_nowait(QueueBackendDelivery(b"job", "receipt", "reply"))

  with TestClient(Queue(backend=backend)) as client:
    requested = client.post("/channels/jobs/request?timeout=2", content=b"question")
    consumed = client.post("/channels/jobs/consumers/worker")
    responded = client.post(
      "/deliveries/respond",
      content=b"answer",
      headers={
        "micro-receipt": consumed.headers["micro-receipt"],
        "micro-reply": consumed.headers["micro-reply"],
      },
    )

  assert requested.content == b"response"
  assert backend.requests == [("jobs", b"question", 2.0)]
  assert consumed.content == b"job"
  assert responded.status_code == 204
  assert backend.settlements == [("respond", "receipt", "reply", b"answer")]


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


def test_queue_client_requests_consumes_and_settles_through_queue_server() -> None:
  calls: list[tuple[str, str, bytes]] = []
  empty_poll = True

  def respond(request: httpx2.Request) -> httpx2.Response:
    nonlocal empty_poll
    calls.append((request.method, request.url.path, request.read()))
    if request.url.path.endswith("/request"):
      return httpx2.Response(200, content=b"answer")
    if "/consumers/" in request.url.path:
      if empty_poll:
        empty_poll = False
        return httpx2.Response(204)
      return httpx2.Response(
        200,
        content=b"job",
        headers={"micro-receipt": "receipt", "micro-reply": "reply"},
      )
    return httpx2.Response(204)

  async def exercise() -> None:
    async with QueueClient(transport=httpx2.MockTransport(respond)) as client:
      client.apply_state(
        {
          "revision": 0,
          "queues": [{"id": "queue-1", "base_url": "http://queue.internal"}],
        }
      )
      assert await client.request("jobs", b"question") == b"answer"
      delivery = await client.consume("jobs", "worker")
      assert delivery.payload == b"job"
      await delivery.respond(b"result")
      with pytest.raises(RuntimeError, match="already been settled"):
        await delivery.acknowledge()

  asyncio.run(exercise())
  assert calls == [
    ("POST", "/channels/jobs/request", b"question"),
    ("POST", "/channels/jobs/consumers/worker", b""),
    ("POST", "/channels/jobs/consumers/worker", b""),
    ("POST", "/deliveries/respond", b"result"),
  ]
