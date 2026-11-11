"""The few ref methods that are more than one operation (see refs.py, generated)."""

from collections.abc import Mapping
from dataclasses import replace
from datetime import datetime
from typing import TYPE_CHECKING, Any

import micro.discord.models.http as m
from micro.discord.ui import Draft
from micro.result import Err, Ok, Result

if TYPE_CHECKING:
  from micro.discord.api import DiscordAPI
  from micro.discord.http_service import DiscordAPIError
  from micro.discord.models import http as m


class _MemberExtras:
  """Mixed into `MemberRef`."""

  api: DiscordAPI
  guild_id: str
  user_id: str

  async def timeout(
    self, until: datetime | str | None, *, reason: str | None = None
  ) -> Any:
    """Silence the member until a time (at most 28 days ahead); None lifts it."""
    when = until.isoformat() if isinstance(until, datetime) else until
    return await self.api.update_guild_member(
      self.guild_id, self.user_id, communication_disabled_until=when, reason=reason
    )


class _MessageExtras:
  """Mixed into `MessageRef`."""

  api: DiscordAPI
  channel_id: str
  message_id: str

  async def reply(
    self, message: Draft | str
  ) -> Result[m.MessageResponse, DiscordAPIError]:
    """Reply to this message in its channel (the `Draft` gets `reply_to` set to it)."""
    return await self.api.create_message(
      self.channel_id, replace(Draft.of(message), reply_to=self.message_id)
    )


class _UserExtras:
  """Mixed into `UserRef`."""

  api: DiscordAPI
  user_id: str

  async def send(
    self, message: Draft | str
  ) -> Result[m.MessageResponse, DiscordAPIError]:
    """Direct-message the user: opens the DM channel, then sends to it.

    The first refusal (the DM could not be opened, or the message was refused) is
    the `Err` you get back.
    """
    match await self.api.create_dm(recipient_id=self.user_id):
      case Err() as failure:
        return failure
      case Ok(channel):
        # Typed when Discord's answer matches its model, plain JSON when it does not.
        identifier: Any = channel["id"] if isinstance(channel, Mapping) else channel.id
        return await self.api.create_message(
          getattr(identifier, "root", identifier), message
        )
