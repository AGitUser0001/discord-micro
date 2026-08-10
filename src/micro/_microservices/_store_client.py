import json
from collections.abc import Mapping
from typing import Any

import httpx2
from pydantic import JsonValue

from ._client import Instance, MicroserviceClient


class StoreClient(MicroserviceClient):
  """Routes GraphQL operations across stores advertised by the overseer."""

  def __init__(
    self,
    *,
    transport: httpx2.AsyncBaseTransport | None = None,
    timeout: float = 5.0,
  ) -> None:
    super().__init__(transport=transport, timeout=timeout)

  def apply_state(self, state: JsonValue) -> None:
    self.apply_state_collection(state, "stores", self._store_registration)

  def _store_registration(self, store: dict[str, JsonValue]) -> Instance:
    instance_id = store.get("id")
    base_url = store.get("base_url")
    modules = store.get("modules")
    if not isinstance(instance_id, str) or not isinstance(base_url, str):
      raise TypeError("Every store needs string id and base_url fields.")
    if not isinstance(modules, list) or not all(
      isinstance(module, str) for module in modules
    ):
      raise TypeError("Every store needs a string modules list.")
    return self.make_instance(
      instance_id,
      base_url,
      {"format": 1, "kind": "store", "modules": modules},
    )

  async def execute(
    self,
    query: str,
    *,
    variables: Mapping[str, JsonValue] | None = None,
    operation_name: str | None = None,
    module: str | None = None,
  ) -> dict[str, Any]:
    candidates = [
      instance
      for instance in self._instances.values()
      if module is None or module in instance.schema["modules"]
    ]
    instance = self.select(f"store:{module or '*'}", candidates)
    body: dict[str, Any] = {"query": query}
    if variables is not None:
      body["variables"] = dict(variables)
    if operation_name is not None:
      body["operationName"] = operation_name
    content = await self.post(
      instance,
      "/graphql",
      json.dumps(body, separators=(",", ":")).encode(),
    )
    decoded = json.loads(content)
    if not isinstance(decoded, dict):
      raise TypeError("Store returned a non-object GraphQL response.")
    return decoded
