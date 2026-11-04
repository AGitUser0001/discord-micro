import importlib
import pkgutil
import tomllib
from collections.abc import Iterable
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator

from micro.runtime import DEFAULT_NATS_URL, Component


class NatsServerConfig(BaseModel):
  """A local nats-server the supervisor starts when none is reachable."""

  model_config = ConfigDict(extra="forbid")

  enabled: bool = True
  binary: str = "nats-server"
  store_dir: str = ".micro/nats"
  args: list[str] = Field(default_factory=list)


class ProcessConfig(BaseModel):
  """One process group: the components each replica hosts."""

  model_config = ConfigDict(extra="forbid")

  components: list[str] = Field(min_length=1)
  replicas: int = Field(default=1, ge=0)
  env: dict[str, str] = Field(default_factory=dict)


class DeploymentConfig(BaseModel):
  """A deployment described in `micro.toml`."""

  model_config = ConfigDict(extra="forbid")

  name: str = "micro"
  nats: list[str] = Field(default_factory=lambda: [DEFAULT_NATS_URL])
  jetstream_replicas: int = Field(default=1, ge=1)
  nats_server: NatsServerConfig = Field(default_factory=NatsServerConfig)
  processes: dict[str, ProcessConfig] = Field(default_factory=dict)

  @field_validator("nats", mode="before")
  @classmethod
  def _one_or_many(cls, value: Any) -> Any:
    return [value] if isinstance(value, str) else value

  def local_nats(self) -> tuple[str, int] | None:
    """Host and port of the first NATS URL when it points at this machine."""
    url = urlsplit(self.nats[0])
    host = url.hostname or "127.0.0.1"
    if host not in {"127.0.0.1", "localhost", "0.0.0.0", "::1"}:
      return None
    return host, url.port or 4222


def load_config(path: str | Path) -> DeploymentConfig:
  with open(path, "rb") as file:
    return DeploymentConfig.model_validate(tomllib.load(file))


def load_components(targets: Iterable[str]) -> list[Component]:
  """Resolve component targets.

  * `module:attribute`: a component, a list of components, or a zero-argument
    callable (such as a component class) returning either.
  * `package.*`: every component defined at module level in each module of the
    package, in module-name order (the recommended layout's `app.services.*`).
  """
  components: list[Component] = []
  for target in targets:
    if target.endswith(".*"):
      components.extend(_package_components(target.removesuffix(".*")))
      continue
    module_name, _, attribute = target.partition(":")
    if not module_name or not attribute:
      raise ValueError(
        f"Component target {target!r} must look like module:attribute or package.*."
      )
    value: Any = importlib.import_module(module_name)
    for part in attribute.split("."):
      value = getattr(value, part)
    if not isinstance(value, Component) and callable(value):
      value = value()
    items = value if isinstance(value, list | tuple) else [value]
    for item in items:
      if not isinstance(item, Component):
        raise TypeError(f"{target!r} did not produce a Micro component.")
      components.append(item)
  return components


def _package_components(package_name: str) -> list[Component]:
  package = importlib.import_module(package_name)
  paths = getattr(package, "__path__", None)
  if paths is None:
    raise ValueError(f"{package_name!r} is a module, not a package.")
  found: list[Component] = []
  for info in sorted(pkgutil.iter_modules(paths), key=lambda item: item.name):
    if info.name.startswith("_"):
      continue
    module = importlib.import_module(f"{package_name}.{info.name}")
    found.extend(
      value
      for value in vars(module).values()
      if isinstance(value, Component) and value not in found
    )
  return found
