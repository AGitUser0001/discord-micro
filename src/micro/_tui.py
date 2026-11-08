"""A tiny terminal layer for full-screen apps: raw keys in, ANSI frames out.

No dependencies: POSIX uses `termios` and the event loop's reader, Windows uses
`msvcrt` on a thread. Keys arrive as names (`up`, `enter`, `esc`, `backspace`, `tab`,
`ctrl-u`, ...) or the printable character itself.
"""

import asyncio
import contextlib
import os
import sys
import threading
import time
from collections.abc import AsyncIterator, Callable, Iterator
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
    self._loop: asyncio.AbstractEventLoop | None = None
    self._thread: threading.Thread | None = None
    self._watching = False
    self._pending = b""
    self._flusher: asyncio.TimerHandle | None = None

  @staticmethod
  def interactive() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty()

  def size(self) -> tuple[int, int]:
    try:
      size = os.get_terminal_size(self.out.fileno())
    except OSError, ValueError:
      return 80, 24
    return (size.columns or 80, size.lines or 24)

  def _write(self, text: str) -> None:
    """Write every byte even if the terminal is (or becomes) non-blocking.

    A big frame can exceed what the terminal accepts at once; a non-blocking descriptor
    then writes part of it or fails with EAGAIN instead of waiting. Wait until writable.
    """
    self.out.flush()
    if os.name == "nt":
      self.out.write(text)
      self.out.flush()
      return
    import select

    fd = self.out.fileno()
    data = text.encode()
    while data:
      try:
        data = data[os.write(fd, data) :]
      except BlockingIOError:
        select.select([], [fd], [], 1.0)

  def __enter__(self) -> Self:
    self.start()
    return self

  def __exit__(self, *exc: object) -> None:
    self.stop()

  def start(self) -> None:
    """Take the terminal. If anything fails, give it back before the error escapes."""
    try:
      if os.name == "nt":
        os.system("")  # turns on ANSI processing in the Windows console
      with contextlib.suppress(OSError):
        os.set_blocking(
          self.out.fileno(), True
        )  # some event loops leave it non-blocking
      self._write("\x1b[?1049h\x1b[?25l\x1b[2J")
      self._begin_input()
    except BaseException:
      self.stop()
      raise

  def stop(self) -> None:
    self._end_input()
    with contextlib.suppress(Exception):
      self._write("\x1b[?25h\x1b[?1049l")

  @contextlib.contextmanager
  def suspended(self) -> Iterator[None]:
    """Hand the terminal back (to run $EDITOR, say) and take it again afterwards."""
    self.stop()
    try:
      yield
    finally:
      self.start()

  # The keyboard is watched by the event loop. Where a loop cannot watch a terminal
  # (Windows' proactor loop, some kqueue cases) a thread does the blocking reads instead.
  # Either way `_write` copes with a terminal a loop left non-blocking.

  def _begin_input(self) -> None:
    self._loop = loop = asyncio.get_running_loop()
    self._reading = True
    if os.name == "nt":
      self._start_thread(self._windows_reader)
      return
    import termios
    import tty

    fd = sys.stdin.fileno()
    self._saved = termios.tcgetattr(fd)
    tty.setcbreak(fd)
    try:
      loop.add_reader(fd, self._on_readable, fd)
      self._watching = True
    except OSError, NotImplementedError, ValueError:
      self._start_thread(self._posix_reader)

  def _start_thread(self, target: Callable[[], None]) -> None:
    self._thread = threading.Thread(target=target, name="micro.tty", daemon=True)
    self._thread.start()

  def _end_input(self) -> None:
    self._reading = False
    if self._watching and self._loop is not None:
      with contextlib.suppress(Exception):
        self._loop.remove_reader(sys.stdin.fileno())
    self._watching = False
    if self._flusher is not None:
      self._flusher.cancel()
      self._flusher = None
    self._pending = b""
    if self._thread is not None and self._thread is not threading.current_thread():
      self._thread.join(timeout=1.0)
    self._thread = None
    if self._saved is not None:
      import termios

      with contextlib.suppress(Exception):
        termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, self._saved)
      self._saved = None

  def _on_readable(self, fd: int) -> None:
    try:
      data = os.read(fd, 256)
    except BlockingIOError:
      return
    except OSError:
      data = b""
    if not data:  # the terminal went away
      if self._loop is not None:
        self._loop.remove_reader(fd)
      self._watching = False
      self._queue.put_nowait("ctrl-d")
      return
    self._pending += data
    if self._flusher is not None:
      self._flusher.cancel()
      self._flusher = None
    # An escape sequence can arrive in pieces (ssh, tmux): wait briefly for the rest
    # before deciding a lone ESC really is the Escape key.
    if self._pending.endswith(b"\x1b") or self._pending in (b"\x1b[", b"\x1bO"):
      assert self._loop is not None
      self._flusher = self._loop.call_later(0.05, self._flush)
    else:
      self._flush()

  def _flush(self) -> None:
    data, self._pending, self._flusher = self._pending, b"", None
    for key in parse_keys(data.decode(errors="ignore")):
      self._queue.put_nowait(key)

  def _push(self, keys: list[str]) -> None:
    """Hand keys read on a thread to the event loop."""
    loop = self._loop
    if loop is not None and not loop.is_closed():
      for key in keys:
        loop.call_soon_threadsafe(self._queue.put_nowait, key)

  def _posix_reader(self) -> None:
    import select

    fd = sys.stdin.fileno()
    while self._reading:
      try:
        ready, _, _ = select.select([fd], [], [], 0.1)
        if not ready:
          continue
        data = os.read(fd, 256)
      except OSError, ValueError:
        break
      if not data:  # the terminal went away
        self._push(["ctrl-d"])
        break
      # An escape sequence can arrive in pieces (ssh, tmux): wait briefly for the rest
      # before deciding a lone ESC really is the Escape key.
      while data in (b"\x1b", b"\x1b[", b"\x1bO") or data.endswith(b"\x1b"):
        more, _, _ = select.select([fd], [], [], 0.05)
        if not more:
          break
        data += os.read(fd, 256)
      self._push(parse_keys(data.decode(errors="ignore")))

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
    while self._reading:
      if not msvcrt.kbhit():  # pyright: ignore[reportAttributeAccessIssue]
        time.sleep(0.02)
        continue
      char = msvcrt.getwch()  # pyright: ignore[reportAttributeAccessIssue]
      if char in {"\x00", "\xe0"}:
        self._push([arrows.get(msvcrt.getwch(), "")])  # pyright: ignore[reportAttributeAccessIssue]
      else:
        self._push(parse_keys(char))

  async def keys(self) -> AsyncIterator[str]:
    while True:
      key = await self._queue.get()
      if key:
        yield key

  def draw(self, lines: list[str], cursor: tuple[int, int] | None = None) -> None:
    """Paint a frame (each line already fits the width); `cursor` is (row, column)."""
    body = "\x1b[K\r\n".join(lines) + "\x1b[K"
    tail = f"\x1b[{cursor[0] + 1};{cursor[1] + 1}H\x1b[?25h" if cursor else "\x1b[?25l"
    self._write("\x1b[H" + body + "\x1b[J" + tail)


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
