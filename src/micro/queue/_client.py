from collections.abc import Buffer

import httpx2
from pydantic import JsonValue

from micro._microservices import (
  Instance,
  MicroserviceClient,
  QueueSettlementError,
  RemoteMicroserviceError,
)

from ._queue import validate_channel


class QueueClient(MicroserviceClient):
  """Publishes, requests, and consumes exclusively through queue servers."""

  def __init__(
    self,
    *,
    transport: httpx2.AsyncBaseTransport | None = None,
    timeout: float = 5.0,
  ) -> None:
    super().__init__(transport=transport, timeout=timeout)

  def apply_state(self, state: JsonValue) -> None:
    self.apply_state_collection(state, "queues", self._queue_registration)

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

  async def request(
    self,
    channel: str,
    payload: Buffer,
    *,
    timeout: float = 30.0,
  ) -> bytes:
    validate_channel(channel)
    if not 0 < timeout <= 300:
      raise ValueError("Request timeout must be between 0 and 300 seconds.")
    instance = self.select(f"queue:{channel}", list(self._instances.values()))
    response = await self._http.post(
      f"{instance.base_url}/channels/{channel}/request",
      params={"timeout": timeout},
      content=bytes(payload),
      headers={"content-type": "application/octet-stream"},
      timeout=timeout + 1,
    )
    if not response.is_success:
      raise RemoteMicroserviceError(instance.id, response.status_code, response.text)
    return response.content

  async def consume(self, channel: str, consumer: str) -> QueueDelivery:
    validate_channel(channel)
    validate_channel(consumer)
    while True:
      instance = self.select(
        f"queue-consumer:{channel}:{consumer}", list(self._instances.values())
      )
      response = await self._http.post(
        f"{instance.base_url}/channels/{channel}/consumers/{consumer}",
        content=b"",
        timeout=None,
      )
      if not response.is_success:
        raise RemoteMicroserviceError(instance.id, response.status_code, response.text)
      if response.status_code == 204:
        continue
      receipt = response.headers.get("micro-receipt")
      if receipt is None:
        raise QueueSettlementError("Queue delivery omitted its receipt capability.")
      return QueueDelivery(
        self,
        instance,
        response.content,
        receipt,
        response.headers.get("micro-reply"),
      )

  async def settle_delivery(
    self,
    instance: Instance,
    action: str,
    receipt: str,
    reply: str | None = None,
    payload: bytes = b"",
  ) -> None:
    headers = {"micro-receipt": receipt}
    if reply is not None:
      headers["micro-reply"] = reply
    await self.post(
      instance,
      f"/deliveries/{action}",
      payload,
      content_type="application/octet-stream",
      headers=headers,
    )


class QueueDelivery:
  """One remotely consumed queue item with mutually exclusive settlement."""

  def __init__(
    self,
    client: QueueClient,
    instance: Instance,
    payload: bytes,
    receipt: str,
    reply: str | None,
  ) -> None:
    self.payload = payload
    self._client = client
    self._instance = instance
    self._receipt = receipt
    self._reply = reply
    self._settled = False

  async def acknowledge(self) -> None:
    await self._finish("acknowledge")

  async def retry(self, *, delay: float = 0) -> None:
    if not 0 <= delay <= 86400:
      raise ValueError("Retry delay must be 0 through 86400 seconds.")
    await self._finish("retry", query=f"?delay={delay}")

  async def dead_letter(self) -> None:
    await self._finish("dead_letter")

  async def respond(self, payload: Buffer) -> None:
    if self._reply is None:
      raise QueueSettlementError(
        "This queue delivery did not originate from request()."
      )
    await self._finish("respond", self._reply, bytes(payload))

  async def _finish(
    self,
    action: str,
    reply: str | None = None,
    payload: bytes = b"",
    query: str = "",
  ) -> None:
    if self._settled:
      raise QueueSettlementError("Queue delivery has already been settled.")
    await self._client.settle_delivery(
      self._instance,
      f"{action}{query}",
      self._receipt,
      reply,
      payload,
    )
    self._settled = True
