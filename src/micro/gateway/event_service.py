import asyncio

import httpx2
from pydantic import JsonValue
from pydantic_core import from_json, to_json

from micro._microservices import Microservice
from micro.queue import QueueClient
from micro.service import ServiceClient


class GatewayEventService(Microservice):
  """Routes queued Discord dispatches to one replica of each listening service."""

  def __init__(
    self,
    *,
    transport: httpx2.AsyncBaseTransport | None = None,
    timeout: float = 5.0,
  ) -> None:
    self.client = ServiceClient(transport=transport, timeout=timeout)
    self.queue = QueueClient(transport=transport, timeout=timeout)
    self._topology_ready = asyncio.Event()
    self._consumer: asyncio.Task[None] | None = None
    super().__init__("gateway.event_service")

  @property
  def component_ready(self) -> bool:
    return self.client.state_revision >= 0 and self.queue.state_revision >= 0

  def apply_state(self, state: JsonValue) -> None:
    service_snapshot = self.client.state_snapshot()
    queue_snapshot = self.queue.state_snapshot()
    try:
      self.client.apply_state(state)
      self.queue.apply_state(state)
    except Exception:
      self.client.restore_state(service_snapshot)
      self.queue.restore_state(queue_snapshot)
      raise
    self._topology_ready.set()

  async def start(self) -> None:
    self._consumer = asyncio.create_task(
      self._consume(), name="micro.gateway.event_service"
    )

  async def close(self) -> None:
    if self._consumer is not None:
      self._consumer.cancel()
      await asyncio.gather(self._consumer, return_exceptions=True)
      self._consumer = None
    await self.client.aclose()
    await self.queue.aclose()

  async def route(self, item: bytes) -> int:
    decoded = from_json(item)
    if (
      not isinstance(decoded, list)
      or len(decoded) != 2
      or not isinstance(decoded[0], str)
    ):
      raise ValueError("Gateway event items must be [event_name, payload].")
    return await self.client.route_event(decoded[0], to_json(decoded[1]))

  async def _consume(self) -> None:
    await self._topology_ready.wait()
    while True:
      try:
        delivery = await self.queue.consume(
          "gateway.events", "micro-gateway-event-service"
        )
      except asyncio.CancelledError:
        raise
      except Exception:
        await asyncio.sleep(0.1)
        continue
      try:
        await self.route(delivery.payload)
      except ValueError:
        # Redelivery cannot repair an invalid queue item.
        await delivery.acknowledge()
      except Exception:
        await delivery.retry()
      else:
        await delivery.acknowledge()
