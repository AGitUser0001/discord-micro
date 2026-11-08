"""Terminal logging: the same line as always, with colour when a person is reading it.

Colour is on when the stream is a terminal; `NO_COLOR` turns it off and
`FORCE_COLOR` turns it on (for example through a pager or a process manager).
"""

import logging
import os
import sys
from typing import IO

FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"

_RESET = "\x1b[0m"
_DIM = "\x1b[2m"
_LEVELS = {
  logging.DEBUG: "\x1b[36m",
  logging.INFO: "\x1b[32m",
  logging.WARNING: "\x1b[33m",
  logging.ERROR: "\x1b[31m",
  logging.CRITICAL: "\x1b[1;31m",
}


def wants_colour(stream: IO[str]) -> bool:
  if os.environ.get("NO_COLOR"):
    return False
  if os.environ.get("FORCE_COLOR", "0") not in ("", "0"):
    return True
  return stream.isatty() and os.environ.get("TERM") != "dumb"


class ColourFormatter(logging.Formatter):
  """Dim timestamp and logger name, the level in its colour; the message as is."""

  def __init__(self) -> None:
    super().__init__(
      f"{_DIM}%(asctime)s{_RESET} %(levelcolour)s%(levelname)-8s{_RESET}"
      f" {_DIM}%(name)s:{_RESET} %(message)s"
    )

  def format(self, record: logging.LogRecord) -> str:
    record.levelcolour = _LEVELS.get(record.levelno, "")
    return super().format(record)


def _demote_http_requests(record: logging.LogRecord) -> bool:
  """httpx2 logs every request at INFO; that is DEBUG detail (shown with `-v`)."""
  if record.name.startswith("httpx2") and record.levelno == logging.INFO:
    record.levelno, record.levelname = logging.DEBUG, "DEBUG"
    return logging.getLogger().isEnabledFor(logging.DEBUG)
  return True


def configure(level: str | int) -> None:
  handler = logging.StreamHandler(sys.stderr)
  if wants_colour(handler.stream):
    handler.setFormatter(ColourFormatter())
  else:
    handler.setFormatter(logging.Formatter(FORMAT))
  handler.addFilter(_demote_http_requests)
  logging.basicConfig(level=level, handlers=[handler])
