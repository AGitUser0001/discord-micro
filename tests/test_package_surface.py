import importlib
import tomllib
from pathlib import Path


def test_every_public_package_imports_with_the_all_extra_environment() -> None:
  for module in (
    "micro.discord.interactions",
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
    "import sys; import micro.service, micro.gateway, micro.discord, micro.runtime, micro.discord.interactions; "
    "assert 'micro.store' not in sys.modules and 'graphql' not in sys.modules, "
    "sorted(m for m in sys.modules if m.startswith(('micro.store', 'graphql')))"
  )
  subprocess.run([sys.executable, "-c", code], check=True)


def test_generated_models_load_only_what_is_used() -> None:
  import subprocess
  import sys

  code = """
import sys
def generated():
  return [m for m in sys.modules if m.startswith("micro.discord.models.") and m.count(".") == 4]
import micro.discord.interactions, micro.service, micro.gateway, micro.discord
from micro.discord import DiscordHTTPClient
assert generated() == [], generated()
assert "hikari" not in sys.modules
from micro.schemas import events
assert generated() == []
events.MESSAGE_CREATE.decode_json  # touching one schema loads only its models
loaded = len(generated())
assert 0 < loaded < 300, loaded
"""
  subprocess.run([sys.executable, "-c", code], check=True)


def test_services_do_not_load_aiohttp_or_httpx() -> None:
  import subprocess
  import sys

  code = """
import sys
import micro.discord.interactions
from micro.discord import DiscordHTTPClient
assert "aiohttp" not in sys.modules and "httpx2" not in sys.modules, sorted(
  m for m in ("aiohttp", "httpx2") if m in sys.modules
)
import nats.aio.transport as transport
assert transport.aiohttp is None
import aiohttp  # still importable for Hikari
from micro._slim import restore_websocket_transport
restore_websocket_transport()
assert transport.aiohttp is aiohttp
"""
  subprocess.run([sys.executable, "-c", code], check=True)
