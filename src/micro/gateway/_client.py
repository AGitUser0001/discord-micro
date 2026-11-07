from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from nats.errors import NoRespondersError
from nats.errors import TimeoutError as NatsTimeoutError
from pydantic import BaseModel

from micro import subjects
from micro.coordination import Table
from micro.errors import RemoteError, RequestTimeoutError, RoutingError
from micro.runtime import Registration, Runtime

from ._control import (
  ActivityUpdate,
  GatewayGeneration,
  GuildMembersRequest,
  PresenceUpdate,
  ShardLease,
  VoiceStateUpdate,
)
from ._worker import ACTIVE_KEY, DESIRED_KEY, PRESENCE_KEY, WORKER_KIND, lease_key


@dataclass(frozen=True, slots=True)
class GatewayStatus:
  """A snapshot of the Gateway: desired and active generation and every shard lease."""

  desired: GatewayGeneration | None
  active: GatewayGeneration | None
  leases: dict[str, ShardLease]
  workers: tuple[Registration, ...]


class GatewayControl:
  """Operates the Gateway from anywhere: control calls, presence, and generations."""

  def __init__(self, runtime: Runtime, *, timeout: float = 5.0) -> None:
    self.runtime = runtime
    self.timeout = timeout

  async def _generations(self) -> Table[GatewayGeneration]:
    return await self.runtime.table(subjects.GATEWAY_BUCKET, GatewayGeneration)

  async def status(self) -> GatewayStatus:
    """Generations, shard leases and owners, as a `GatewayStatus`."""
    generations = await self._generations()
    desired = await generations.get(DESIRED_KEY)
    active = await generations.get(ACTIVE_KEY)
    shards = await self.runtime.table(
      subjects.SHARDS_BUCKET, ShardLease, ttl_markers=True
    )
    leases = {key: value.value for key, value in (await shards.items()).items()}
    return GatewayStatus(
      desired.value if desired else None,
      active.value if active else None,
      leases,
      self.runtime.directory.entries(WORKER_KIND),
    )

  async def set_shard_count(self, shard_count: int) -> GatewayGeneration:
    """Start a new generation with `shard_count` shards beside the current one."""
    return await self._new_generation(shard_count)

  async def roll(self) -> GatewayGeneration:
    """Replace every connection with a new generation of the same size."""
    return await self._new_generation(None)

  async def _new_generation(self, shard_count: int | None) -> GatewayGeneration:
    generations = await self._generations()
    while True:
      current = await generations.get(DESIRED_KEY)
      if current is None:
        generation = GatewayGeneration(id=1, shard_count=shard_count or 1)
        if await generations.create(DESIRED_KEY, generation) is not None:
          await generations.create(ACTIVE_KEY, generation)
          return generation
        continue
      generation = GatewayGeneration(
        id=current.value.id + 1,
        shard_count=shard_count or current.value.shard_count,
      )
      if (
        await generations.update(DESIRED_KEY, generation, revision=current.revision)
        is not None
      ):
        return generation

  async def update_presence(
    self,
    *,
    status: str = "online",
    activity: ActivityUpdate | None = None,
    idle_since: datetime | None = None,
    afk: bool = False,
  ) -> None:
    """Set the bot's presence on every current and future shard connection."""
    update = PresenceUpdate.model_validate(
      {"status": status, "activity": activity, "idle_since": idle_since, "afk": afk}
    )
    table = await self.runtime.table(subjects.GATEWAY_BUCKET, PresenceUpdate)
    await table.put(PRESENCE_KEY, update)

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
    """Ask the owner of the guild's shard to request members from Discord."""
    request = GuildMembersRequest(
      guild_id=guild_id,
      include_presences=include_presences,
      query=query,
      limit=limit,
      users=tuple(users) if users is not None else None,
      nonce=nonce,
    )
    await self._send(guild_id, "members", request)

  async def update_voice_state(
    self,
    guild_id: int,
    channel_id: int | None,
    *,
    self_mute: bool = False,
    self_deaf: bool = False,
  ) -> None:
    """Ask the owner of the guild's shard to join, move or leave a voice channel."""
    update = VoiceStateUpdate(
      guild_id=guild_id, channel_id=channel_id, self_mute=self_mute, self_deaf=self_deaf
    )
    await self._send(guild_id, "voice", update)

  async def shard_for(self, guild_id: int) -> int:
    """The shard id a guild belongs to in the active generation."""
    active = await (await self._generations()).get(ACTIVE_KEY)
    if active is None:
      raise RoutingError("No Gateway generation is active.")
    return (guild_id >> 22) % active.value.shard_count

  async def connection_for(self, guild_id: int) -> str | None:
    """The READY connection publishing the guild's shard, if any."""
    active = await (await self._generations()).get(ACTIVE_KEY)
    if active is None:
      return None
    shards = await self.runtime.table(
      subjects.SHARDS_BUCKET, ShardLease, ttl_markers=True
    )
    shard_id = (guild_id >> 22) % active.value.shard_count
    lease = await shards.get(lease_key(active.value.id, shard_id))
    if lease is None or not lease.value.ready:
      return None
    return lease.value.connection_id

  async def _send(self, guild_id: int, operation: str, command: BaseModel) -> None:
    shard_id = await self.shard_for(guild_id)
    try:
      reply = await self.runtime.nats.request(
        subjects.gateway_control(shard_id, operation),
        command.model_dump_json().encode(),
        timeout=self.timeout,
      )
    except NoRespondersError as exc:
      raise RoutingError(f"No Gateway worker owns shard {shard_id}.") from exc
    except NatsTimeoutError as exc:
      raise RequestTimeoutError(f"Gateway {operation} timed out.") from exc
    if (reply.headers or {}).get("Micro-Status") == "error":
      raise RemoteError(f"gateway.{operation}", "handler_failed", reply.data.decode())
