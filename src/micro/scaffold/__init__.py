"""Add Micro to a Python project, however it is managed (uv, pip, ...).

The packaging tool owns the project (interpreter, dependencies, layout);
Micro only adds its own pieces. Examples are packages (see `micro.scaffold.packages`):
fetched from a git source, copied in, yours to edit, upgradable.

    pip install discord-micro    # or: uv add discord-micro
    micro init                   # micro.toml + services/hello/
    micro services add tickets   # services/tickets/ (a new, empty service)
"""

import logging
import re
import tomllib
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from string import Template

from . import packages


@dataclass(frozen=True, slots=True)
class Project:
  root: Path
  name: str
  services: Path
  """Directory holding one module per service."""
  target: str
  """The micro.toml component target loading every service."""


def _project_name(root: Path) -> str:
  pyproject = root / "pyproject.toml"
  if pyproject.is_file():
    with open(pyproject, "rb") as file:
      name = tomllib.load(file).get("project", {}).get("name")
    if isinstance(name, str) and name:
      return name
  return root.name


def _layout(root: Path, name: str) -> Project:
  """Services go in the project's package if it has a src/ layout, else in services/."""
  package = re.sub(r"[-.]", "_", name).lower()
  candidates = [package] if (root / "src" / package / "__init__.py").is_file() else []
  if not candidates and (root / "src").is_dir():
    candidates = sorted(p.parent.name for p in (root / "src").glob("*/__init__.py"))
  if len(candidates) == 1:
    package = candidates[0]
    return Project(
      root, name, root / "src" / package / "services", f"{package}.services.*"
    )
  return Project(root, name, root / "services", "services.*")


def locate(start: Path | None = None) -> Project:
  """The project to set up: the nearest directory with pyproject.toml, else `start`."""
  here = (start or Path.cwd()).resolve()
  root = next(
    (p for p in (here, *here.parents) if (p / "pyproject.toml").is_file()), here
  )
  return _layout(root, _project_name(root))


def find(start: Path | None = None) -> Project:
  """The Micro project around `start`: the nearest directory with micro.toml.

  Services live where micro.toml's `...services.*` target points.
  """
  here = (start or Path.cwd()).resolve()
  root = next((p for p in (here, *here.parents) if (p / "micro.toml").is_file()), None)
  if root is None:
    raise FileNotFoundError("No micro.toml here; run `micro init` first.")
  with open(root / "micro.toml", "rb") as file:
    config = tomllib.load(file)
  name = str(config.get("name") or _project_name(root))
  for process in (config.get("processes") or {}).values():
    for target in process.get("components", []):
      if isinstance(target, str) and target.endswith("services.*"):
        parts = target.removesuffix(".*").split(".")
        if len(parts) == 1:
          return Project(root, name, root / parts[0], target)
        for base in (root / "src", root):
          if base.joinpath(*parts[:-1]).is_dir():
            return Project(root, name, base.joinpath(*parts), target)
  return _layout(root, name)


def _render(template: str, values: dict[str, str]) -> str:
  source = resources.files("micro.scaffold") / "templates" / template
  return Template(source.read_text()).substitute(values)


def add_service(project: Project, name: str) -> Path:
  """A new, empty service: services/NAME/ with one slash command. Yours from the start."""
  key = packages._key(name)  # pyright: ignore[reportPrivateUsage]
  folder = project.services / key
  taken = packages.Lock.load(project).entries
  if key in taken or folder.exists() or (project.services / f"{key}.py").exists():
    raise FileExistsError(f"{folder} already exists.")
  values = packages._values(name)  # pyright: ignore[reportPrivateUsage]
  folder.mkdir(parents=True)
  (folder / "__init__.py").write_text(_render("service/__init__.py.tmpl", values))
  return folder


def init(start: Path | None = None) -> Project:
  """Add micro.toml to the current project, and the `hello` package when it can be fetched."""
  project = locate(start)
  config = project.root / "micro.toml"
  if config.exists():
    raise FileExistsError(f"{config} already exists.")
  values = {
    "name": project.name,
    "target": project.target,
    "directory": str(project.services.relative_to(project.root)),
  }
  project.services.mkdir(parents=True, exist_ok=True)
  package = project.services / "__init__.py"
  if not package.exists():
    package.write_text(_render("services/__init__.py.tmpl", values))
  config.write_text(_render("micro.toml.tmpl", values))
  if not (project.services / "hello").exists():
    try:
      packages.add("builtin/hello", project)
    except (packages.FETCH_ERRORS, ValueError, OSError) as error:
      logging.getLogger("micro").warning(
        "Could not add the hello package (%s). Add it when you are online: "
        "`micro pkg add builtin/hello`.",
        error,
      )
  ignore = project.root / ".gitignore"
  existing = ignore.read_text() if ignore.exists() else ""
  missing = [entry for entry in (".micro/", ".env") if entry not in existing.split()]
  if missing:
    separator = "" if not existing or existing.endswith("\n") else "\n"
    ignore.write_text(existing + separator + "".join(f"{entry}\n" for entry in missing))
  return project


__all__ = (
  "Project",
  "add_service",
  "find",
  "init",
  "locate",
  "packages",
)
