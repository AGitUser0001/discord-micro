"""Add Micro to a Python project, however it is managed (uv, pip, ...).

The packaging tool owns the project (interpreter, dependencies, layout);
Micro only adds its own pieces. Templates ship with Micro and update with it.

    pip install micro    # or: uv add micro
    micro init           # micro.toml + services/hello/
    micro add service tickets    # services/tickets/
"""

import re
import tomllib
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from string import Template
from typing import Any

_NAME = re.compile(r"[a-z][a-z0-9-]*[a-z0-9]|[a-z]")


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


def init(start: Path | None = None) -> Project:
  """Add micro.toml and a `hello` service to the current project."""
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
  for template, path in (
    ("services/__init__.py.tmpl", project.services / "__init__.py"),
    ("services/hello.py.tmpl", project.services / "hello" / "__init__.py"),
  ):
    if not path.exists():
      path.parent.mkdir(parents=True, exist_ok=True)
      path.write_text(_render(template, values))
  config.write_text(_render("micro.toml.tmpl", values))
  ignore = project.root / ".gitignore"
  existing = ignore.read_text() if ignore.exists() else ""
  missing = [entry for entry in (".micro/", ".env") if entry not in existing.split()]
  if missing:
    separator = "" if not existing or existing.endswith("\n") else "\n"
    ignore.write_text(existing + separator + "".join(f"{entry}\n" for entry in missing))
  return project


def add_service(name: str, start: Path | None = None) -> Path:
  """Add a service folder; the services target loads it without config changes."""
  if _NAME.fullmatch(name) is None:
    raise ValueError("Service names use lowercase letters, digits, and hyphens.")
  project = find(start)
  module = name.replace("-", "_")
  folder = project.services / module
  if folder.exists() or (project.services / f"{module}.py").exists():
    raise FileExistsError(f"{folder} already exists.")
  folder.mkdir(parents=True)
  path = folder / "__init__.py"
  path.write_text(
    _render("service.py.tmpl", {"name": name, "command": name, "function": module})
  )
  return folder


def examples() -> dict[str, str]:
  """Bundled examples (one folder each) and their one-line descriptions."""
  folder = resources.files("micro.scaffold") / "examples"
  found: dict[str, str] = {}
  for item in sorted(folder.iterdir(), key=lambda entry: entry.name):
    if item.is_dir() and not item.name.startswith(("_", ".")):
      text = (item / "__init__.py").read_text()
      summary = (
        text.split('"""')[1].strip().splitlines()[0] if text.startswith('"""') else ""
      )
      found[item.name] = summary
  return found


def add_example(name: str, start: Path | None = None) -> Path:
  """Copy a bundled example into the services as a folder of its own."""
  available = examples()
  if name not in available:
    raise ValueError(f"No example {name!r}; choose from: {', '.join(available)}.")
  project = find(start)
  target = project.services / name
  if target.exists() or (project.services / f"{name}.py").exists():
    raise FileExistsError(f"{target} already exists.")
  project.services.mkdir(parents=True, exist_ok=True)
  _copy(resources.files("micro.scaffold") / "examples" / name, target)
  return target


def _copy(source: Any, target: Path) -> None:
  target.mkdir()
  for item in source.iterdir():
    if item.name == "__pycache__":
      continue
    if item.is_dir():
      _copy(item, target / item.name)
    else:
      (target / item.name).write_bytes(item.read_bytes())


__all__ = (
  "Project",
  "add_example",
  "add_service",
  "examples",
  "find",
  "init",
  "locate",
)
