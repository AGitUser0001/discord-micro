import asyncio
from collections.abc import Sequence

import httpx2
from pydantic import JsonValue

from ._client import Instance, MicroserviceClient, NoCompatibleInstanceError
from ._gateway_control import (
  ActivityUpdate,
  GuildMembersRequest,
  PresenceUpdate,
  VoiceStateUpdate,
)


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
    shard_ids = gateway.get("shard_ids", [])
    shard_count = gateway.get("shard_count")
    if not isinstance(instance_id, str) or not isinstance(base_url, str):
      raise TypeError("Every gateway needs string id and base_url fields.")
    if not isinstance(shard_ids, list) or any(
      isinstance(shard_id, bool) or not isinstance(shard_id, int)
      for shard_id in shard_ids
    ):
      raise TypeError("Every gateway needs an integer shard_ids list.")
    if shard_count is not None and (
      isinstance(shard_count, bool) or not isinstance(shard_count, int)
    ):
      raise TypeError("Gateway shard_count must be an integer or null.")
    return self.make_instance(
      instance_id,
      base_url,
      {
        "format": 1,
        "kind": "gateway",
        "shard_ids": shard_ids,
        "shard_count": shard_count,
      },
    )

  async def update_presence(
    self,
    *,
    status: str = "online",
    idle_since: object | None = None,
    activity: ActivityUpdate | None = None,
    afk: bool = False,
  ) -> None:
    update = PresenceUpdate.model_validate(
      {
        "status": status,
        "idle_since": idle_since,
        "activity": activity,
        "afk": afk,
      }
    )
    instances = list(self._instances.values())
    if not instances:
      raise NoCompatibleInstanceError("No gateway instances are available.")
    body = update.model_dump_json().encode()
    await asyncio.gather(
      *(self.post(instance, "/gateway/presence", body) for instance in instances)
    )

  async def request_guild_members(
    self,
    guild_id: int,
    *,
    include_presences: bool = False,
    query: str | None = None,
    limit: int = 0,
    users: Sequence[int] | None = None,
    nonce: str | None = None,
  ) -> None:
    request = GuildMembersRequest(
      guild_id=guild_id,
      include_presences=include_presences,
      query=query,
      limit=limit,
      users=tuple(users) if users is not None else None,
      nonce=nonce,
    )
    await self._post_for_guild(
      guild_id, "/gateway/guild-members", request.model_dump_json().encode()
    )

  async def update_voice_state(
    self,
    guild_id: int,
    channel_id: int | None,
    *,
    self_mute: bool = False,
    self_deaf: bool = False,
  ) -> None:
    update = VoiceStateUpdate(
      guild_id=guild_id,
      channel_id=channel_id,
      self_mute=self_mute,
      self_deaf=self_deaf,
    )
    await self._post_for_guild(
      guild_id, "/gateway/voice-state", update.model_dump_json().encode()
    )

  async def _post_for_guild(self, guild_id: int, path: str, body: bytes) -> None:
    candidates = [
      instance
      for instance in self._instances.values()
      if _owns_guild(instance, guild_id)
    ]
    instance = self.select(f"gateway:guild:{guild_id}", candidates)
    await self.post(instance, path, body)


def _owns_guild(instance: Instance, guild_id: int) -> bool:
  shard_count = instance.schema["shard_count"]
  shard_ids = instance.schema["shard_ids"]
  return (
    isinstance(shard_count, int)
    and shard_count > 0
    and (guild_id >> 22) % shard_count in shard_ids
  )
