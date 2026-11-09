"""Sending messages with safe defaults (mentions never ping unless allowed)."""

from collections.abc import Mapping, Sequence
from dataclasses import replace
from typing import TYPE_CHECKING, Protocol

from pydantic import JsonValue

from micro.discord.objects import Message
from micro.discord.ui import (
  AllowedMentions,
  Buildable,
  Draft,
  Embed,
  Json,
  Upload,
)

if TYPE_CHECKING:
  from micro.discord import DiscordHTTPClient


async def send(
  http: DiscordHTTPClient,
  channel_id: int | str,
  content: Draft | str | None = None,
  *,
  embeds: Sequence[Embed | Json] | None = None,
  components: Sequence[Buildable] | None = None,
  allowed_mentions: AllowedMentions | None = None,
  reply_to: int | str | None = None,
  files: Sequence[Upload] = (),
) -> Message:
  """Send a message (a `Draft`, or its pieces) to a channel through the HTTP workers,
  with safe mention defaults.

  `files` are attached; an `Upload` shown by a component or an embed is attached by
  itself.
  """
  from micro.discord.interactions._context import uploads

  draft = Draft.of(
    content,
    embeds=embeds,
    components=components,
    files=files,
    allowed_mentions=allowed_mentions,
  )
  if reply_to is not None:
    draft = replace(draft, reply_to=reply_to)
  result = await http.call(
    "create_message",
    path={"channel_id": str(channel_id)},
    body=draft.to_dict(),
    files=uploads(draft.uploads),
  )
  return Message.model_validate(result)


class _Addressed(Protocol):
  """Anything with a message's `id` and `channel_id` (a `Message`, a dispatch model)."""

  @property
  def id(self) -> str: ...
  @property
  def channel_id(self) -> str: ...


async def reply_to(
  http: DiscordHTTPClient,
  message: _Addressed | Mapping[str, JsonValue],
  content: Draft | str | None = None,
  *,
  embeds: Sequence[Embed | Json] | None = None,
  components: Sequence[Buildable] | None = None,
  allowed_mentions: AllowedMentions | None = None,
  files: Sequence[Upload] = (),
) -> Message:
  """Reply to a received message (a MESSAGE_CREATE payload or `Message`)."""
  if isinstance(message, Mapping):
    channel, identifier = str(message["channel_id"]), str(message["id"])
  else:
    channel, identifier = message.channel_id, message.id
  return await send(
    http,
    channel,
    content,
    embeds=embeds,
    components=components,
    allowed_mentions=allowed_mentions,
    reply_to=identifier,
    files=files,
  )


__all__ = ("reply_to", "send")
