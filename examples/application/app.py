"""A small Discord bot built from independently replaceable services.

Every object below is a component. `micro.toml` runs them all in one process;
`micro.multi.toml` spreads the same objects over several processes. The
router and command sync are builtin templates listed in the config.
"""

import asyncio
from typing import Annotated

from pydantic import BaseModel, Field

from micro.discord import DiscordHTTPClient
from micro.discord.filters import all_of, content_startswith, ignore_bots
from micro.discord.interactions import (
  Commands,
  Components,
  CustomId,
  Interaction,
  Modals,
  Option,
)
from micro.discord.messages import reply_to
from micro.discord.models.gateway import GatewayMessageCreateDispatchData
from micro.discord.objects import Member
from micro.discord.ui import AllowedMentions, Button, Modal, TextInput, embed
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


# Talks to Discord: `!ping`, slash commands, a button, a modal, a user command.
bot = Service("bot")
commands = Commands(bot)
components = Components(bot)
modals = Modals(bot)


@bot.listen(
  discord.MESSAGE_CREATE, when=all_of(ignore_bots, content_startswith("!ping"))
)
async def ping(message: GatewayMessageCreateDispatchData) -> None:
  await reply_to(DiscordHTTPClient(bot.runtime), message, "pong")


@commands.slash("greet", description="Greet someone")
async def greet_command(
  ctx: Interaction,
  name: Annotated[str, Option("Who to greet")],
  shout: bool = False,
) -> None:
  reply = (await bot.client.request(GREET, Greeting(name=name))).message
  await ctx.reply(reply.upper() if shout else reply)


@greet_command.autocomplete("name")
async def suggest_names(ctx: Interaction, value: str) -> list[str]:
  names = ("Ada", "Grace", "Linus", "Margaret")
  return [name for name in names if name.lower().startswith(value.lower())]


class Poll(BaseModel):
  question: str
  choice: int


VOTE = CustomId("example.vote", Poll)
FEEDBACK = CustomId("example.feedback")

polls = commands.group("poll", description="Quick polls")


@polls.command("start", description="Start a yes/no poll")
async def start_poll(
  ctx: Interaction, question: Annotated[str, Option("The question", max_length=60)]
) -> None:
  await ctx.reply(
    embeds=[embed(question, "Vote below.")],
    components=[
      Button(
        "Yes", custom_id=VOTE.encode(Poll(question=question, choice=1)), style="success"
      ),
      Button(
        "No", custom_id=VOTE.encode(Poll(question=question, choice=0)), style="danger"
      ),
    ],
  )


@components.on(VOTE)
async def vote(ctx: Interaction, poll: Poll) -> None:
  answer = "yes" if poll.choice else "no"
  await ctx.reply(
    f"{ctx.user.display_name} voted {answer} on {poll.question!r}.", ephemeral=True
  )


@commands.slash("feedback", description="Tell us what you think")
async def ask_feedback(ctx: Interaction) -> None:
  await ctx.modal(
    Modal(
      FEEDBACK.encode(),
      "Feedback",
      [TextInput("text", "Your thoughts", style="paragraph")],
    )
  )


@modals.on(FEEDBACK)
async def feedback(ctx: Interaction) -> None:
  await bot.client.enqueue(AUDIT, Greeting(name=f"feedback: {ctx.fields['text'][:40]}"))
  await ctx.reply("Thanks for the feedback!", ephemeral=True)


@commands.user("Say hi")
async def say_hi(ctx: Interaction, member: Member) -> None:
  mentions = AllowedMentions.only(users=[int(member.id or 0)])
  await ctx.reply(f"Hi {member.mention}!", allowed_mentions=mentions)


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
