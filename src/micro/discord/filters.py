"""Predicates for `Service.listen(..., when=...)` on Discord dispatches.

service.listen(events.MESSAGE_CREATE, when=all_of(ignore_bots, in_channel(123)))
"""

from collections.abc import Callable, Mapping

type Predicate = Callable[[object], bool]


def _field(value: object, name: str) -> object:
  if value is None:
    return None
  if isinstance(value, Mapping):
    return value.get(name)  # pyright: ignore[reportUnknownMemberType]
  return getattr(value, name, None)


def author(payload: object) -> object:
  """The author of a message, or the user of a member-carrying event."""
  return (
    _field(payload, "author")
    or _field(_field(payload, "member"), "user")
    or _field(payload, "user")
  )


def ignore_bots(payload: object) -> bool:
  """False for events authored by bots (including this one)."""
  return not _field(author(payload), "bot")


def not_from(*user_ids: int | str) -> Predicate:
  """False for events authored by these users (pass the bot's ID to ignore itself)."""
  ids = {str(user) for user in user_ids}
  return lambda payload: str(_field(author(payload), "id")) not in ids


def from_users(*user_ids: int | str) -> Predicate:
  """True only for events authored by one of these users."""
  ids = {str(user) for user in user_ids}
  return lambda payload: str(_field(author(payload), "id")) in ids


def in_channel(*channel_ids: int | str) -> Predicate:
  """True only for events in one of these channels."""
  ids = {str(channel) for channel in channel_ids}
  return lambda payload: str(_field(payload, "channel_id")) in ids


def in_guild(*guild_ids: int | str) -> Predicate:
  """True only for events in one of these guilds."""
  ids = {str(guild) for guild in guild_ids}
  return lambda payload: str(_field(payload, "guild_id")) in ids


def content_startswith(*prefixes: str) -> Predicate:
  """True for a message whose content starts with the prefix."""
  return lambda payload: str(_field(payload, "content") or "").startswith(prefixes)


def all_of(*predicates: Predicate) -> Predicate:
  """True when every predicate is true."""
  return lambda payload: all(predicate(payload) for predicate in predicates)


def any_of(*predicates: Predicate) -> Predicate:
  """True when any predicate is true."""
  return lambda payload: any(predicate(payload) for predicate in predicates)


__all__ = (
  "Predicate",
  "all_of",
  "any_of",
  "author",
  "content_startswith",
  "from_users",
  "ignore_bots",
  "in_channel",
  "in_guild",
  "not_from",
)
