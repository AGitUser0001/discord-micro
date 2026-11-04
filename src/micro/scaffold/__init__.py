"""Project setup in Micro's recommended layout.

Templates ship with Micro, so a project created by a newer Micro gets the
newer layout.

    project/
      pyproject.toml          depends on micro
      micro.toml              discord plumbing + `<package>.services.*`
      src/<package>/services/ one module per service
"""

import json
import re
import tomllib
from importlib import metadata, resources
from importlib.resources.abc import Traversable
from pathlib import Path
from string import Template

_NAME = re.compile(r"[a-z][a-z0-9-]*[a-z0-9]|[a-z]")
_PACKAGE_DIR = "__package__"


def _validate(name: str, what: str) -> str:
  if _NAME.fullmatch(name) is None:
    raise ValueError(
      f"{what} names use lowercase letters, digits, and hyphens, starting with a letter."
    )
  return name


def package_name(name: str) -> str:
  return name.replace("-", "_")


def _requirement() -> tuple[str, str]:
  """The dependency on this Micro, and a uv source if it was installed locally."""
  try:
    distribution = metadata.distribution("micro")
  except metadata.PackageNotFoundError:
    return "micro[all,accel]", ""
  requirement = f"micro[all,accel]>={distribution.version}"
  direct = distribution.read_text("direct_url.json")
  if direct:
    url = json.loads(direct).get("url", "")
    if url.startswith("file://"):
      path = url.removeprefix("file://")
      return requirement, f'\n[tool.uv.sources]\nmicro = {{ path = "{path}" }}\n'
  return requirement, ""


def _render(template: Traversable, values: dict[str, str]) -> str:
  return Template(template.read_text()).substitute(values)


def _files(root: Traversable, prefix: Path = Path()) -> list[tuple[Path, Traversable]]:
  found: list[tuple[Path, Traversable]] = []
  for item in sorted(root.iterdir(), key=lambda entry: entry.name):
    if item.is_dir():
      found += _files(item, prefix / item.name)
    elif item.name.endswith(".tmpl"):
      found.append((prefix / item.name.removesuffix(".tmpl"), item))
  return found


def init(name: str, directory: Path | None = None) -> Path:
  """Create a project named `name` (in `directory`, default `./name`)."""
  _validate(name, "Project")
  target = (directory or Path(name)).resolve()
  if target.exists() and any(target.iterdir()):
    raise FileExistsError(f"{target} exists and is not empty.")
  requirement, sources = _requirement()
  package = package_name(name)
  values = {
    "name": name,
    "package": package,
    "requirement": requirement,
    "sources": sources,
  }
  templates = resources.files("micro.scaffold") / "templates" / "project"
  for relative, template in _files(templates):
    path = Path(*(package if part == _PACKAGE_DIR else part for part in relative.parts))
    if path.name == "gitignore":
      path = path.with_name(".gitignore")
    destination = target / path
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(_render(template, values))
  return target


def find_project(start: Path | None = None) -> Path:
  """The nearest directory holding micro.toml and pyproject.toml."""
  here = (start or Path.cwd()).resolve()
  for candidate in (here, *here.parents):
    if (candidate / "micro.toml").is_file() and (
      candidate / "pyproject.toml"
    ).is_file():
      return candidate
  raise FileNotFoundError("No Micro project here (micro.toml and pyproject.toml).")


def add_service(name: str, project: Path | None = None) -> Path:
  """Add `src/<package>/services/<name>.py`; `<package>.services.*` loads it."""
  _validate(name, "Service")
  root = find_project(project)
  with open(root / "pyproject.toml", "rb") as file:
    package = package_name(tomllib.load(file)["project"]["name"])
  module = package_name(name)
  path = root / "src" / package / "services" / f"{module}.py"
  if path.exists():
    raise FileExistsError(f"{path} already exists.")
  template = resources.files("micro.scaffold") / "templates" / "service.py.tmpl"
  path.parent.mkdir(parents=True, exist_ok=True)
  path.write_text(
    _render(template, {"name": name, "command": name, "function": module})
  )
  return path


__all__ = ("add_service", "find_project", "init", "package_name")
