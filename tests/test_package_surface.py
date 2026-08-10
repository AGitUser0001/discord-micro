import importlib
import tomllib
from pathlib import Path


def test_every_public_package_imports_with_the_all_extra_environment() -> None:
  for module in (
    "micro.client",
    "micro.discord",
    "micro.gateway",
    "micro.overseer",
    "micro.queue",
    "micro.schemas",
    "micro.service",
    "micro.store",
  ):
    assert importlib.import_module(module) is not None


def test_optional_dependency_groups_are_independently_declared() -> None:
  metadata = tomllib.loads(Path("pyproject.toml").read_text())
  extras = metadata["project"]["optional-dependencies"]
  assert set(extras) >= {
    "accel",
    "all",
    "client",
    "gateway",
    "overseer",
    "queue",
    "service",
    "store",
    "uvloop",
    "winloop",
  }
