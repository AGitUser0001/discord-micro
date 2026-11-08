"""A tiny terminal layer for full-screen apps: raw keys in, ANSI frames out.

No dependencies: POSIX uses `termios` and the event loop's reader, Windows uses
`msvcrt` on a thread. Keys arrive as names (`up`, `enter`, `esc`, `backspace`, `tab`,
`ctrl-u`, ...) or the printable character itself.
"""

import asyncio
import contextlib
import os
import sys
from collections.abc import AsyncIterator, Iterator
from typing import Any, Self, TextIO

_SEQUENCES = {
  "\x1b[A": "up",
  "\x1b[B": "down",
  "\x1b[C": "right",
  "\x1b[D": "left",
  "\x1b[H": "home",
  "\x1b[F": "end",
  "\x1b[1~": "home",
  "\x1b[4~": "end",
  "\x1bOH": "home",
  "\x1bOF": "end",
  "\x1b[3~": "delete",
  "\x1b[5~": "pageup",
  "\x1b[6~": "pagedown",
  "\x1b[Z": "shift-tab",
}
_SINGLE = {
  "\r": "enter",
  "\n": "enter",
  "\t": "tab",
  "\x7f": "backspace",
  "\x08": "backspace",
  "\x1b": "esc",
  "\x15": "ctrl-u",
  "\x03": "ctrl-c",
  "\x04": "ctrl-d",
}


def parse_keys(data: str) -> list[str]:
  """Split what one read returned into key names."""
  keys: list[str] = []
  index = 0
  while index < len(data):
    if data[index] == "\x1b":
      for length in (4, 3):
        name = _SEQUENCES.get(data[index : index + length])
        if name is not None:
          keys.append(name)
          index += length
          break
      else:
        # A bare ESC, or a sequence we do not know (skipped whole).
        if data[index + 1 : index + 2] in {"[", "O"}:
          end = index + 2
          while end < len(data) and not data[end].isalpha() and data[end] != "~":
            end += 1
          index = end + 1
        else:
          keys.append("esc")
          index += 1
      continue
    keys.append(_SINGLE.get(data[index], data[index]))
    index += 1
  return keys


class Terminal:
  """Raw keyboard input and a full-screen display; use it as a context manager."""

  def __init__(self, out: TextIO | None = None) -> None:
    self.out = out or sys.stdout
    self._queue: asyncio.Queue[str] = asyncio.Queue()
    self._saved: Any = None
    self._reading = False

  @staticmethod
  def interactive() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty()

  def size(self) -> tuple[int, int]:
    size = os.get_terminal_size(self.out.fileno()) if self.out.isatty() else None
    return (size.columns, size.lines) if size else (80, 24)

  def __enter__(self) -> Self:
    self.start()
    return self

  def __exit__(self, *exc: object) -> None:
    self.stop()

  def start(self) -> None:
    if os.name == "nt":
      os.system("")  # turns on ANSI processing in the Windows console
    self.out.write("\x1b[?1049h\x1b[?25l\x1b[2J")
    self.out.flush()
    self._begin_input()

  def stop(self) -> None:
    self._end_input()
    self.out.write("\x1b[?25h\x1b[?1049l")
    self.out.flush()

  @contextlib.contextmanager
  def suspended(self) -> Iterator[None]:
    """Hand the terminal back (to run $EDITOR, say) and take it again afterwards."""
    self.stop()
    try:
      yield
    finally:
      self.start()

  def _begin_input(self) -> None:
    if os.name == "nt":
      self._reading = True
      asyncio.get_running_loop().run_in_executor(None, self._windows_reader)
      return
    import termios
    import tty

    fd = sys.stdin.fileno()
    self._saved = termios.tcgetattr(fd)
    tty.setcbreak(fd)
    asyncio.get_running_loop().add_reader(fd, self._read_posix, fd)

  def _end_input(self) -> None:
    if os.name == "nt":
      self._reading = False
      return
    import termios

    fd = sys.stdin.fileno()
    with contextlib.suppress(Exception):
      asyncio.get_running_loop().remove_reader(fd)
    if self._saved is not None:
      termios.tcsetattr(fd, termios.TCSADRAIN, self._saved)
      self._saved = None

  def _read_posix(self, fd: int) -> None:
    data = os.read(fd, 256).decode(errors="ignore")
    for key in parse_keys(data):
      self._queue.put_nowait(key)

  def _windows_reader(self) -> None:  # pragma: no cover - Windows only
    import msvcrt

    arrows = {
      "H": "up",
      "P": "down",
      "K": "left",
      "M": "right",
      "G": "home",
      "O": "end",
    }
    loop = asyncio.get_event_loop()
    while self._reading:
      char = msvcrt.getwch()  # pyright: ignore[reportAttributeAccessIssue]
      if char in {"\x00", "\xe0"}:
        loop.call_soon_threadsafe(
          self._queue.put_nowait,
          arrows.get(msvcrt.getwch(), ""),  # pyright: ignore[reportAttributeAccessIssue]
        )
      else:
        for key in parse_keys(char):
          loop.call_soon_threadsafe(self._queue.put_nowait, key)

  async def keys(self) -> AsyncIterator[str]:
    while True:
      key = await self._queue.get()
      if key:
        yield key

  def draw(self, lines: list[str], cursor: tuple[int, int] | None = None) -> None:
    """Paint a frame (each line already fits the width); `cursor` is (row, column)."""
    body = "\x1b[K\r\n".join(lines) + "\x1b[K"
    tail = f"\x1b[{cursor[0] + 1};{cursor[1] + 1}H\x1b[?25h" if cursor else "\x1b[?25l"
    self.out.write("\x1b[H" + body + "\x1b[J" + tail)
    self.out.flush()


def fit(text: str, width: int) -> str:
  """Cut to `width` columns, ending in an ellipsis; pad shorter text with spaces."""
  if width <= 0:
    return ""
  if len(text) > width:
    return text[: max(width - 1, 0)] + "…"
  return text.ljust(width)


REVERSE = "\x1b[7m"
BOLD = "\x1b[1m"
DIM = "\x1b[2m"
RED = "\x1b[31m"
GREEN = "\x1b[32m"
CYAN = "\x1b[36m"
YELLOW = "\x1b[33m"
RESET = "\x1b[0m"


def style(text: str, *codes: str) -> str:
  return "".join(codes) + text + RESET if codes else text
