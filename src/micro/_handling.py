"""What Micro wraps around every handler: its place in the log, and its results."""

from collections.abc import Iterator
from contextlib import ExitStack, contextmanager

from micro import log
from micro.result import handling as watched_results


@contextmanager
def handling(*path: str, **fields: object) -> Iterator[None]:
  """Run a handler with its call path and fields on every log line it makes, and
  fail it if it leaves an `Err` unlooked-at (see `micro.result`)."""
  with ExitStack() as stack:
    stack.enter_context(log.context(**fields))
    for segment in path:
      stack.enter_context(log.step(segment))
    stack.enter_context(watched_results())
    yield
