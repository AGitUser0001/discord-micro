import json

import httpx2
from pydantic import JsonValue

from ._client import Instance, MicroserviceClient


class GatewayClient(MicroserviceClient):
  """Routes control requests to gateway instances advertised by the overseer."""

  def __init__(
    self,
    *,
    transport: httpx2.AsyncBaseTransport | None = None,
    timeout: float = 5.0,
  ) -> None:
    super().__init__(transport=transport, timeout=timeout)

  def apply_state(self, state: JsonValue) -> None:
    self._apply_state_collection(state, "gateways", self._gateway_registration)

  def _gateway_registration(self, gateway: dict[str, JsonValue]) -> Instance:
    instance_id = gateway.get("id")
    base_url = gateway.get("base_url")
    if not isinstance(instance_id, str) or not isinstance(base_url, str):
      raise TypeError("Every gateway needs string id and base_url fields.")
    return self.make_instance(
      instance_id,
      base_url,
      {"format": 1, "kind": "gateway"},
    )

  async def request(self, path: str, payload: JsonValue) -> bytes:
    instance = self.select("gateway", list(self._instances.values()))
    return await self.post(
      instance,
      path,
      json.dumps(payload, separators=(",", ":")).encode(),
    )
