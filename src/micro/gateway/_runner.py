import asyncio
import importlib
from typing import Protocol, cast


class _EventLoopModule(Protocol):
  def new_event_loop(self) -> asyncio.AbstractEventLoop: ...


def event_loop_factory() -> asyncio.AbstractEventLoop:
  """Create the fastest installed supported event loop."""
  for module_name in ("uvloop", "winloop"):
    try:
      module = importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
      if exc.name != module_name:
        raise
    else:
      return cast(_EventLoopModule, module).new_event_loop()
  return asyncio.new_event_loop()
