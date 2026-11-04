"""A small Discord bot built from independently replaceable services.

Every object below is a component. `micro.toml` runs them all in one process;
`micro.multi.toml` spreads the same objects over several processes.
"""

import asyncio
from typing import Annotated

from pydantic import BaseModel, Field

from micro.discord import DiscordHTTPClient
from micro.discord.models.gateway import GatewayMessageCreateDispatchData
from micro.discord.models.http import (
  CreateMessageParametersPath,
  CreateMessageRequest,
  MessageAllowedMentionsRequest,
  SnowflakeType,
)
from micro.discord.models.http_requests import CreateMessageHTTPRequest
from micro.runtime import Component
from micro.schemas import events as discord
from micro.service import EventSchema, RequestSchema, Service, WorkQueue


class Greeting(BaseModel):
  name: Annotated[str, Field(min_length=1)]


class GreetingReply(BaseModel):
  message: str


class Tick(BaseModel):
  count: int


GREET = RequestSchema[Greeting, GreetingReply](
  id="example.greet", input=Greeting, output=GreetingReply
)
GREETED = EventSchema[Greeting](id="example.greeted", payload=Greeting)
TICKED = EventSchema[Tick](id="example.ticked", payload=Tick)
AUDIT = WorkQueue[Greeting]("example.audit", Greeting)

# Answers `example.greet` and tells everyone who listens.
greeter = Service("greeter")


@greeter.handle(GREET)
async def greet(request: Greeting) -> GreetingReply:
  await greeter.client.emit(GREETED, request)
  return GreetingReply(message=f"Hello, {request.name}!")


# Listens to application events and records them durably.
audit = Service("audit")


@audit.listen(GREETED)
async def greeted(event: Greeting) -> None:
  await audit.client.enqueue(AUDIT, event)


@audit.work(AUDIT)
async def record(job: Greeting) -> None:
  print(f"audit: greeted {job.name}")


@audit.listen(TICKED)
async def ticked(event: Tick) -> None:
  print(f"audit: tick {event.count}")


# Talks to Discord: replies to `!ping` and `!greet NAME`.
bot = Service("bot")


@bot.listen(discord.MESSAGE_CREATE, when=lambda m: m.content.startswith("!"))
async def command(message: GatewayMessageCreateDispatchData) -> None:
  if message.author.bot:
    return
  if message.content == "!ping":
    reply = "pong"
  elif message.content.startswith("!greet "):
    name = message.content.removeprefix("!greet ").strip() or message.author.username
    reply = (await bot.client.request(GREET, Greeting(name=name))).message
  else:
    return
  await DiscordHTTPClient(bot.runtime).create_message(
    CreateMessageHTTPRequest(
      path=CreateMessageParametersPath(channel_id=SnowflakeType(message.channel_id)),
      body=CreateMessageRequest(
        content=reply, allowed_mentions=MessageAllowedMentionsRequest(parse=[])
      ),
    )
  )


class Ticker(Component):
  """A background task: emits a tick every minute while it runs."""

  def __init__(self) -> None:
    super().__init__("ticker")

  async def on_start(self) -> None:
    self.spawn(self._tick(), name="tick")

  async def _tick(self) -> None:
    from micro.service import Client

    client = Client(self.runtime)
    count = 0
    while self.active:
      count += 1
      await client.emit(TICKED, Tick(count=count))
      await asyncio.sleep(60)


ticker = Ticker()
