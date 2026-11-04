"""Keep nats-py from importing aiohttp, which Micro does not use.

nats-py imports aiohttp (about 14 MB) whenever it is installed, only to offer
its WebSocket transport. Micro connects over TCP, and aiohttp is often present
only because Hikari depends on it. This one-shot import hook hides aiohttp
while `nats.aio.transport` executes and then unhides it, so Hikari and anything
else can still import it normally. `Runtime` restores the WebSocket transport
when a `ws://` or `wss://` server is configured.
"""

import importlib.abc
import importlib.machinery
import sys
from types import ModuleType
from typing import Any

_TARGET = "nats.aio.transport"
_HIDDEN = ("aiohttp", "multidict")


class _Loader(importlib.abc.Loader):
  def __init__(self, loader: Any) -> None:
    self._loader = loader

  def create_module(self, spec: importlib.machinery.ModuleSpec) -> ModuleType | None:
    return self._loader.create_module(spec)

  def exec_module(self, module: ModuleType) -> None:
    hidden = [name for name in _HIDDEN if name not in sys.modules]
    for name in hidden:
      sys.modules[name] = None  # type: ignore[assignment]  # makes `import` raise ImportError
    try:
      self._loader.exec_module(module)
    finally:
      for name in hidden:
        if sys.modules.get(name, ...) is None:
          del sys.modules[name]


class _Finder(importlib.abc.MetaPathFinder):
  def find_spec(
    self, fullname: str, path: Any, target: ModuleType | None = None
  ) -> importlib.machinery.ModuleSpec | None:
    if fullname != _TARGET:
      return None
    sys.meta_path.remove(self)
    spec = importlib.machinery.PathFinder.find_spec(fullname, path)
    if spec is not None and spec.loader is not None:
      spec.loader = _Loader(spec.loader)
    return spec


def install() -> None:
  if _TARGET not in sys.modules and not any(
    isinstance(f, _Finder) for f in sys.meta_path
  ):
    sys.meta_path.insert(0, _Finder())


def restore_websocket_transport() -> None:
  """Give nats-py its WebSocket transport back (imports aiohttp)."""
  transport = sys.modules.get(_TARGET)
  if transport is not None and getattr(transport, "aiohttp", None) is None:
    import aiohttp
    import multidict

    transport.aiohttp = aiohttp  # type: ignore[attr-defined]
    transport.multidict = multidict  # type: ignore[attr-defined]
