"""Discord features: `!ping`, slash commands, buttons, a modal, a user command."""

from typing import Annotated

from pydantic import BaseModel

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
from micro.discord.objects import Member
from micro.discord.ui import AllowedMentions, Button, Modal, TextInput, embed
from micro.schemas import events
from micro.service import Service

from ._contracts import AUDIT, GREET, Greeting

service = Service("chat")
commands = Commands(service)
components = Components(service)
modals = Modals(service)


@service.listen(
  events.MESSAGE_CREATE, when=all_of(ignore_bots, content_startswith("!ping"))
)
async def ping(message: object) -> None:
  await reply_to(DiscordHTTPClient(service.runtime), message, "pong")


@commands.slash("greet", description="Greet someone")
async def greet(
  ctx: Interaction, name: Annotated[str, Option("Who to greet")], shout: bool = False
) -> None:
  reply = (await service.client.request(GREET, Greeting(name=name))).message
  await ctx.respond(reply.upper() if shout else reply)


@greet.autocomplete("name")
async def suggest(ctx: Interaction, value: str) -> list[str]:
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
  yes = VOTE.encode(Poll(question=question, choice=1))
  no = VOTE.encode(Poll(question=question, choice=0))
  await ctx.respond(
    embeds=[embed(question, "Vote below.")],
    components=[
      Button("Yes", custom_id=yes, style="success"),
      Button("No", custom_id=no, style="danger"),
    ],
  )


@components.on(VOTE)
async def vote(ctx: Interaction, poll: Poll) -> None:
  answer = "yes" if poll.choice else "no"
  await ctx.respond(
    f"{ctx.user.display_name} voted {answer} on {poll.question!r}.", ephemeral=True
  )


@commands.slash("feedback", description="Tell us what you think")
async def ask_feedback(ctx: Interaction) -> None:
  text = TextInput("text", "Your thoughts", style="paragraph")
  await ctx.modal(Modal(FEEDBACK.encode(), "Feedback", [text]))


@modals.on(FEEDBACK)
async def feedback(ctx: Interaction) -> None:
  await service.client.enqueue(
    AUDIT, Greeting(name=f"feedback: {ctx.fields['text'][:40]}")
  )
  await ctx.respond("Thanks for the feedback!", ephemeral=True)


@commands.user("Say hi")
async def say_hi(ctx: Interaction, member: Member) -> None:
  mentions = AllowedMentions.only(users=[int(member.id or 0)])
  await ctx.respond(f"Hi {member.mention}!", allowed_mentions=mentions)
