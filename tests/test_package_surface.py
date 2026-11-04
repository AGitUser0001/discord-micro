import importlib
import tomllib
from pathlib import Path


def test_every_public_package_imports_with_the_all_extra_environment() -> None:
  for module in (
    "micro.cli",
    "micro.coordination",
    "micro.discord",
    "micro.errors",
    "micro.gateway",
    "micro.gateway.projection",
    "micro.http",
    "micro.launch",
    "micro.queue",
    "micro.runtime",
    "micro.schemas",
    "micro.service",
    "micro.store",
    "micro.subjects",
  ):
    assert importlib.import_module(module) is not None


def test_optional_dependency_groups_are_independently_declared() -> None:
  metadata = tomllib.loads(Path("pyproject.toml").read_text())
  extras = metadata["project"]["optional-dependencies"]
  assert set(extras) == {
    "accel",
    "all",
    "gateway",
    "http",
    "store",
    "uvloop",
    "winloop",
  }
  assert metadata["project"]["scripts"]["micro"] == "micro.cli:main"
  assert any(dep.startswith("nats-py") for dep in metadata["project"]["dependencies"])


def test_builtins_do_not_import_the_store() -> None:
  import subprocess
  import sys

  code = (
    "import sys; import micro.service, micro.gateway, micro.discord, micro.runtime; "
    "assert 'micro.store' not in sys.modules and 'graphql' not in sys.modules, "
    "sorted(m for m in sys.modules if m.startswith(('micro.store', 'graphql')))"
  )
  subprocess.run([sys.executable, "-c", code], check=True)
