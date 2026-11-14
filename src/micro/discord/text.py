"""Small helpers for message text: escaping, mentions, timestamps, snowflakes.

from micro.discord import text

await ctx.respond(f"{text.escape(name)} joined {text.timestamp(when, 'R')}")
"""

import re
from datetime import UTC, datetime
from re import Match
from typing import Literal

DISCORD_EPOCH_MS = 1420070400000
"""Milliseconds between the Unix epoch and Discord's (the first second of 2015)."""

type TimestampStyle = Literal["t", "T", "d", "D", "f", "F", "s", "S", "R"]
"""How Discord shows a timestamp: `t`/`T` time, `d`/`D` date, `f`/`F` date and time,
`s`/`S` short date and time, `R` relative ("3 hours ago")."""

_URL = r"<[^:\s>]+:/[^\s>]+>|(?:https?|steam)://[^\s<]+[^<.,:;\"'\]\s]"
_MARKDOWN = (
  r"(?P<indent>^[ \t]*)(?P<marker>>|#|-)"
  r"|(?P<ordinal>^[ \t]*\d+)(?P<dot>\.)(?=[ \t])"
  r"|(?P<char>[\\*_~|`]|\[(?=[^\n]*\]\([^\n]*\)))"
)
_ESCAPE_MARKDOWN = re.compile(_MARKDOWN, re.MULTILINE)
_ESCAPE_MARKDOWN_KEEP_LINKS = re.compile(rf"(?P<url>{_URL})|{_MARKDOWN}", re.MULTILINE)


def _escape_match(match: Match[str]) -> str:
  if (url := match.groupdict().get("url")) is not None:
    return url
  if (marker := match["marker"]) is not None:
    return f"{match['indent']}\\{marker}"
  if (dot := match["dot"]) is not None:
    return f"{match['ordinal']}\\{dot}"
  return f"\\{match['char']}"


def escape(text: str, *, ignore_links: bool = True) -> str:
  """Escape everything Discord would render as markdown, so `text` shows literally.

  Escapes ``\\ * _ ~ | ```, the ``[`` of a masked link ``[x](y)``, and the markers
  that mean something at the start of a line: ``>`` quotes, ``#`` headings, ``-``
  lists and ``-#`` subtext, and ``1.`` numbered lists. With `ignore_links`, URLs
  and ``<scheme:...>`` links are left untouched. Mentions are not markdown; control
  those with allowed mentions.

  Use it on anything a user typed (names, titles) that goes inside your own formatting.
  """
  pattern = _ESCAPE_MARKDOWN_KEEP_LINKS if ignore_links else _ESCAPE_MARKDOWN
  return pattern.sub(_escape_match, text)


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
