"""Predicates for `Service.listen(..., when=...)` on Discord dispatches.

service.listen(events.MESSAGE_CREATE, when=all_of(ignore_bots, in_channel(123)))
"""

from collections.abc import Callable, Mapping
from typing import Any

type Predicate = Callable[[Any], bool]


def _field(value: Any, name: str) -> Any:
  if value is None:
    return None
  if isinstance(value, Mapping):
    return value.get(name)  # pyright: ignore[reportUnknownMemberType]
  return getattr(value, name, None)


def author(payload: Any) -> Any:
  """The author of a message, or the user of a member-carrying event."""
  return (
    _field(payload, "author")
    or _field(_field(payload, "member"), "user")
    or _field(payload, "user")
  )


def ignore_bots(payload: Any) -> bool:
  """False for events authored by bots (including this one)."""
  return not _field(author(payload), "bot")


def not_from(*user_ids: int | str) -> Predicate:
  """False for events authored by these users (pass the bot's ID to ignore itself)."""
  ids = {str(user) for user in user_ids}
  return lambda payload: str(_field(author(payload), "id")) not in ids


def from_users(*user_ids: int | str) -> Predicate:
  ids = {str(user) for user in user_ids}
  return lambda payload: str(_field(author(payload), "id")) in ids


def in_channel(*channel_ids: int | str) -> Predicate:
  ids = {str(channel) for channel in channel_ids}
  return lambda payload: str(_field(payload, "channel_id")) in ids


def in_guild(*guild_ids: int | str) -> Predicate:
  ids = {str(guild) for guild in guild_ids}
  return lambda payload: str(_field(payload, "guild_id")) in ids


def content_startswith(*prefixes: str) -> Predicate:
  return lambda payload: str(_field(payload, "content") or "").startswith(prefixes)


def all_of(*predicates: Predicate) -> Predicate:
  return lambda payload: all(predicate(payload) for predicate in predicates)


def any_of(*predicates: Predicate) -> Predicate:
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
