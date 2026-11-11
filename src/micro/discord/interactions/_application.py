"""The `Context`: what a handler uses to reach Discord, separate from the interaction."""

from functools import cached_property
from typing import TYPE_CHECKING

if TYPE_CHECKING:
  from micro.discord.api import DiscordAPI
  from micro.discord.http_service import DiscordHTTPClient
  from micro.discord.state import DiscordState
  from micro.gateway import GatewayControl
  from micro.scheduler import Timers
  from micro.service import Client, Service
  from micro.store import StoreClient


class Context:
  """The master object of a bot: everything a handler uses to reach Discord and your own
  services, separate from the interaction it is handling (and from the runtime).

  A handler asks for it by annotation, with the interaction beside it:

      @commands.slash("whois")
      async def whois(ctx: Context, interaction: Interaction, who: User) -> None:
        member = await ctx.state.member(interaction.guild_id, who.id)
        await interaction.respond(f"{member.display_name}")

  `ctx.api` calls Discord; `ctx.state` reads what the Gateway connections know;
  `ctx.gateway` controls the connections (status, voice, member lists); `ctx.timers`
  schedules things for later; `ctx.store` keeps your records; `ctx.client` talks to your own services.
  """

  def __init__(
    self,
    http: DiscordHTTPClient,
    *,
    service: Service | None = None,
    application_id: str | None = None,
  ) -> None:
    self.http = http
    """The client every Discord request goes through (`ctx.api` is its API)."""
    self.application_id = application_id
    """The id of your application (the bot), when the context comes from an interaction."""
    self._service = service

  @cached_property
  def api(self) -> DiscordAPI:
    """Every Discord operation as a method: `await ctx.api.create_message(...)`."""
    return self.http.api

  @cached_property
  def state(self) -> DiscordState:
    """What the Gateway connections know of Discord: guilds, roles, channels, members,
    users, the bot itself (`await ctx.state.member(guild_id, user_id)`). It never asks
    Discord."""
    from micro.discord.state import DiscordState

    return DiscordState(self.http.runtime, context=self)

  @cached_property
  def gateway(self) -> GatewayControl:
    """The Gateway connections: `await ctx.gateway.update_presence(...)`, `status()`,
    `update_voice_state(...)`, `request_guild_members(...)`, intents and shards."""
    from micro.gateway import GatewayControl

    return GatewayControl(self.http.runtime)

  @cached_property
  def timers(self) -> Timers:
    """Things to happen later: `await ctx.timers.event(...)`, `job`, `cancel`, `pending`."""
    from micro.scheduler import Timers

    return Timers(self.http.runtime)

  @cached_property
  def store(self) -> StoreClient:
    """The Store: your durable records, in your own typed schema, with your own queries
    (`await ctx.store.execute("{ guild(id: ...) { ... } }")`). Needs a Store process."""
    from micro.store import StoreClient

    return StoreClient(self.http.runtime)

  @property
  def client(self) -> Client:
    """The client for your own services: `await ctx.client.request(...)`, `emit`, `enqueue`.

    Raises:
      RuntimeError: This context belongs to no service (it was built by hand).
    """
    if self._service is None:
      raise RuntimeError("This Context belongs to no service, so it has no client.")
    return self._service.client
