"""The few ref methods that are more than one operation (see refs.py, generated)."""

from collections.abc import Mapping
from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
  from micro.discord.api import DiscordAPI


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


class _UserExtras:
  """Mixed into `UserRef`."""

  api: DiscordAPI
  user_id: str

  async def send(self, content: str | None = None, **message: Any) -> Any:
    """Direct-message the user: opens the DM channel, then sends to it."""
    channel: Any = await self.api.create_dm(recipient_id=self.user_id)
    identifier = channel["id"] if isinstance(channel, Mapping) else channel.id
    identifier = getattr(identifier, "root", identifier)
    return await self.api.create_message(identifier, content=content, **message)
