"""A small service: a slash command and a button with typed state."""

from pydantic import BaseModel

from micro.discord import (
  Button,
  Commands,
  Components,
  Context,
  CustomId,
  Draft,
  Interaction,
)
from micro.service import Service

service = Service("hello")
commands = Commands(service)
components = Components(service)


class Wave(BaseModel):
  name: str


WAVE = CustomId("hello.wave", Wave)


@commands.slash("hello", description="Say hello")
async def hello(ctx: Context, interaction: Interaction, name: str = "world") -> None:
  await interaction.respond(
    Draft(
      f"Hello, {name}!",
      components=[Button("Wave back", custom_id=WAVE.encode(Wave(name=name)))],
    )
  )


@components.match(WAVE)
async def wave(ctx: Context, interaction: Interaction, state: Wave) -> None:
  await interaction.respond(
    Draft(f"{interaction.user.display_name} waves at {state.name}.", ephemeral=True)
  )
