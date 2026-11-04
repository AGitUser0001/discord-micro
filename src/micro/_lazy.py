"""Lazy package exports: import a submodule only when one of its names is used."""

from collections.abc import Callable, Mapping
from importlib import import_module
from typing import Any


def exports(
  package: str, names: Mapping[str, str]
) -> tuple[Callable[[str], Any], Callable[[], list[str]]]:
  """Return `__getattr__` and `__dir__` for a package.

  `names` maps each exported name to the submodule (relative, like `.client`)
  that defines it; a name mapped to itself as `.name` exports the submodule.
  """

  def __getattr__(name: str) -> Any:
    try:
      module = names[name]
    except KeyError:
      raise AttributeError(f"module {package!r} has no attribute {name!r}") from None
    loaded = import_module(module, package)
    value = loaded if module == f".{name}" else getattr(loaded, name)
    import sys

    setattr(sys.modules[package], name, value)
    return value

  def __dir__() -> list[str]:
    return sorted(names)

  return __getattr__, __dir__
