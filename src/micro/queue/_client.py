from collections.abc import Buffer

import httpx2
from pydantic import JsonValue

from micro._microservices import MicroserviceClient
from micro._microservices._client import Instance

from ._queue import validate_channel


class QueueClient(MicroserviceClient):
  """Routes publications across queue ingress instances."""

  def __init__(
    self,
    *,
    transport: httpx2.AsyncBaseTransport | None = None,
    timeout: float = 5.0,
  ) -> None:
    super().__init__(transport=transport, timeout=timeout)

  def apply_state(self, state: JsonValue) -> None:
    self._apply_state_collection(state, "queues", self._queue_registration)

  def _queue_registration(self, queue: dict[str, JsonValue]) -> Instance:
    instance_id = queue.get("id")
    base_url = queue.get("base_url")
    if not isinstance(instance_id, str) or not isinstance(base_url, str):
      raise TypeError("Every queue needs string id and base_url fields.")
    return self.make_instance(
      instance_id,
      base_url,
      {"format": 1, "kind": "queue"},
    )

  async def publish(self, channel: str, payload: Buffer) -> None:
    validate_channel(channel)
    instance = self.select(f"queue:{channel}", list(self._instances.values()))
    await self.post(
      instance,
      f"/channels/{channel}",
      bytes(payload),
      content_type="application/octet-stream",
    )
