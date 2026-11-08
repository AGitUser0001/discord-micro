"""Sending messages with safe defaults (mentions never ping unless allowed)."""

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from micro.discord.objects import Message
from micro.discord.ui import AllowedMentions, Buildable, Json, message_body

if TYPE_CHECKING:
  from micro.discord import DiscordHTTPClient


async def send(
  http: DiscordHTTPClient,
  channel_id: int | str,
  content: str | None = None,
  *,
  embeds: Sequence[Json] = (),
  components: Sequence[Buildable] | None = None,
  allowed_mentions: AllowedMentions | None = None,
  reply_to: int | str | None = None,
) -> Message:
  """Send a message to a channel through the HTTP workers, with safe mention defaults."""
  body = message_body(
    content, embeds=embeds, components=components, allowed_mentions=allowed_mentions
  )
  if reply_to is not None:
    body["message_reference"] = {
      "message_id": str(reply_to),
      "fail_if_not_exists": False,
    }
  result = await http.call(
    "create_message", path={"channel_id": str(channel_id)}, body=body
  )
  return Message.model_validate(result)


async def reply_to(
  http: DiscordHTTPClient, message: Any, content: str | None = None, **options: Any
) -> Message:
  """Reply to a received message (a MESSAGE_CREATE payload or `Message`)."""
  channel = message["channel_id"] if isinstance(message, dict) else message.channel_id
  identifier = message["id"] if isinstance(message, dict) else message.id
  return await send(http, channel, content, reply_to=identifier, **options)


__all__ = ("reply_to", "send")
