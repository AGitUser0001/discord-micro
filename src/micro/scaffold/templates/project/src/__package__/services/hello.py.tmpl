"""A small service: a slash command and a button with typed state."""

from pydantic import BaseModel

from micro.discord.interactions import Commands, Components, CustomId, Interaction
from micro.discord.ui import Button
from micro.service import Service

service = Service("hello")
commands = Commands(service)
components = Components(service)


class Wave(BaseModel):
  name: str


WAVE = CustomId("hello.wave", Wave)


@commands.slash("hello", description="Say hello")
async def hello(ctx: Interaction, name: str = "world") -> None:
  await ctx.reply(
    f"Hello, {name}!",
    components=[Button("Wave back", custom_id=WAVE.encode(Wave(name=name)))],
  )


@components.on(WAVE)
async def wave(ctx: Interaction, state: Wave) -> None:
  await ctx.reply(f"{ctx.user.display_name} waves at {state.name}.", ephemeral=True)
