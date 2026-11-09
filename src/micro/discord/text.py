"""Small helpers for message text: escaping, mentions, timestamps, snowflakes.

from micro.discord import text

await ctx.respond(f"{text.escape(name)} joined {text.timestamp(when, 'R')}")
"""

import re
from datetime import UTC, datetime
from typing import Literal

DISCORD_EPOCH_MS = 1420070400000
"""Milliseconds between the Unix epoch and Discord's (the first second of 2015)."""

type TimestampStyle = Literal["t", "T", "d", "D", "f", "F", "s", "S", "R"]
"""How Discord shows a timestamp: `t`/`T` time, `d`/`D` date, `f`/`F` date and time,
`s`/`S` short date and time, `R` relative ("3 hours ago")."""

_MARKDOWN = re.compile(r"([\\*_~`|>#\-\[\]()])")
_LINE_START = re.compile(r"^(\s*)(\d+)\.(\s)", re.MULTILINE)


def escape(text: str) -> str:
  """`text` with Discord's Markdown switched off, so it shows exactly as written.

  Use it on anything a user typed (names, titles) that goes inside your own formatting.
  """
  return _LINE_START.sub(r"\1\2\\.\3", _MARKDOWN.sub(r"\\\1", text))


def escape_mentions(text: str) -> str:
  """`text` with `@everyone`, `@here` and `<@...>` mentions made inert.

  Messages sent through Micro already ping nobody unless `allowed_mentions` says so;
  this is for text that must also not *look* like a mention.
  """
  text = re.sub(r"@(everyone|here)", "@\u200b\\1", text)
  return re.sub(r"<(@[!&]?|#)(\d+)>", "<\\1\u200b\\2>", text)


def timestamp(when: datetime | float, style: TimestampStyle = "f") -> str:
  """A timestamp every reader sees in their own time zone: `<t:1700000000:R>`.

  `when` is an aware datetime or a Unix time in seconds.
  """
  if isinstance(when, datetime):
    if when.tzinfo is None:
      raise ValueError("timestamp() needs a timezone-aware datetime.")
    when = when.timestamp()
  return f"<t:{int(when)}:{style}>"


def user(user_id: int | str) -> str:
  """A user mention: `<@id>`."""
  return f"<@{user_id}>"


def role(role_id: int | str) -> str:
  """A role mention: `<@&id>`."""
  return f"<@&{role_id}>"


def channel(channel_id: int | str) -> str:
  """A channel link: `<#id>`."""
  return f"<#{channel_id}>"


def command(name: str, command_id: int | str) -> str:
  """A clickable slash command: `</name:id>` (`name` may include a subcommand)."""
  return f"</{name}:{command_id}>"


def snowflake_time(snowflake: int | str) -> datetime:
  """When a Discord id was created (every id carries its creation time)."""
  return datetime.fromtimestamp(((int(snowflake) >> 22) + DISCORD_EPOCH_MS) / 1000, UTC)


def time_snowflake(when: datetime, *, high: bool = False) -> int:
  """The lowest id created at `when` (the highest, with `high`), for `before=`/`after=`."""
  if when.tzinfo is None:
    raise ValueError("time_snowflake() needs a timezone-aware datetime.")
  milliseconds = int(when.timestamp() * 1000) - DISCORD_EPOCH_MS
  return (milliseconds << 22) + ((1 << 22) - 1 if high else 0)


__all__ = (
  "DISCORD_EPOCH_MS",
  "TimestampStyle",
  "channel",
  "command",
  "escape",
  "escape_mentions",
  "role",
  "snowflake_time",
  "time_snowflake",
  "timestamp",
  "user",
)
