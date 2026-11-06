"""Packages: services Micro ships that you copy into your project and then own.

A package comes from a source, a folder of packages. The default source is the
builtin one inside Micro (the examples, the starter `hello`, the blank `service`
template); `[sources]` in micro.toml names others. `add` copies a package into the
project's services and
`micro.lock` records the hash of every file as it was copied. The files are yours
to edit, so `upgrade` compares three things per file: the recorded hash (what Micro
last gave you), the file now, and what this Micro ships. It changes only what you
have not touched and reports the rest, so nothing you wrote is overwritten without
being asked.

    micro pkg add chat                 # services/chat/
    micro pkg add service tickets      # a template takes a name
    micro pkg status                   # what a newer Micro would change
    micro pkg upgrade                  # apply it, keeping your edits
"""

import difflib
import hashlib
import json
import re
import tomllib
from dataclasses import dataclass, field
from importlib import resources
from importlib.resources.abc import Traversable
from pathlib import Path
from string import Template
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
  from . import Project

BUILTIN = "builtin"
"""The source that ships inside Micro, and the default."""
LOCK = "micro.lock"
"""The file, beside micro.toml, recording the packages added to the project."""

_NAME = re.compile(r"[a-z][a-z0-9-]*[a-z0-9]|[a-z]")
_SKIP = {"__pycache__", "package.toml"}

type Kind = Literal[
  "current",  # your file is what Micro ships
  "refresh",  # same content already; only the record is stale
  "upgrade",  # you never touched it and Micro changed it
  "add",  # Micro ships a new file
  "remove",  # Micro dropped a file you never touched
  "orphan",  # Micro dropped a file you edited: kept
  "dropped",  # Micro dropped a file you had already deleted
  "modified",  # you edited it and Micro did not change it
  "deleted",  # you deleted it and Micro did not change it
  "conflict",  # you and Micro both changed it
  "gone",  # you deleted it and Micro changed it
  "theirs",  # a conflict settled with Micro's version
  "mine",  # a conflict settled by keeping yours
]
ATTENTION: frozenset[Kind] = frozenset({"conflict", "gone"})
"""Kinds that need a decision: `--theirs` or `--mine`."""
PENDING: frozenset[Kind] = frozenset(
  {"upgrade", "add", "remove", "refresh", "orphan", "dropped"}
)
"""Kinds `upgrade` applies on its own."""


def bundled() -> Traversable:
  return resources.files("micro") / "packages"


def configured_sources(project: Project) -> dict[str, str]:
  """The named sources in micro.toml's `[sources]`: name to folder."""
  path = project.root / "micro.toml"
  if not path.is_file():
    return {}
  table = tomllib.loads(path.read_text()).get("sources", {})
  return {str(name): str(folder) for name, folder in table.items()}


def resolve(
  project: Project | None, source: str | None = None
) -> tuple[str, Traversable]:
  """A source's label, as recorded in micro.lock, and its folder of packages.

  The label is `builtin`, a name from `[sources]`, or a folder path.
  """
  label = source or BUILTIN
  if label == BUILTIN:
    return BUILTIN, bundled()
  named = configured_sources(project) if project is not None else {}
  if label not in named and not (set("/\\~.") & {label[0], *label}):
    raise ValueError(
      f"No package source named {label!r}. Name one under [sources] in micro.toml, "
      "or pass a folder."
    )
  folder = Path(named.get(label, label)).expanduser()
  if not folder.is_absolute() and project is not None:
    folder = project.root / folder
  if not folder.is_dir():
    raise FileNotFoundError(f"Package source {label!r}: {folder} is not a folder.")
  return label, folder


def _version() -> str:
  from importlib.metadata import PackageNotFoundError, version

  try:
    return version("discord-micro")
  except PackageNotFoundError:
    return "unknown"


def _hash(data: bytes) -> str:
  return "sha256:" + hashlib.sha256(data).hexdigest()


# What Micro ships --------------------------------------------------------------


def available(source: Traversable | None = None) -> dict[str, str]:
  """Package names and one-line descriptions."""
  root = source or bundled()
  found: dict[str, str] = {}
  for item in sorted(root.iterdir(), key=lambda entry: entry.name):
    if item.is_dir() and not item.name.startswith(("_", ".")):
      found[item.name] = _describe(item)
  return found


def _describe(folder: Traversable) -> str:
  meta = folder / "package.toml"
  if meta.is_file():
    text = tomllib.loads(meta.read_text()).get("description")
    if isinstance(text, str):
      return text
  init = folder / "__init__.py"
  if init.is_file():
    text = init.read_text()
    if text.startswith('"""'):
      return text.split('"""')[1].strip().splitlines()[0]
  return ""


def _files(
  folder: Traversable, values: dict[str, str], prefix: str = ""
) -> dict[str, bytes]:
  """A package's files as they would be written: `.tmpl` files filled in."""
  found: dict[str, bytes] = {}
  for item in sorted(folder.iterdir(), key=lambda entry: entry.name):
    if item.name in _SKIP or item.name.startswith("."):
      continue
    if item.is_dir():
      found |= _files(item, values, f"{prefix}{item.name}/")
      continue
    data, name = item.read_bytes(), prefix + item.name
    if name.endswith(".tmpl"):
      data = Template(data.decode()).substitute(values).encode()
      name = name.removesuffix(".tmpl")
    found[name] = data
  return found


def _templated(folder: Traversable) -> bool:
  return any(
    _templated(item) if item.is_dir() else item.name.endswith(".tmpl")
    for item in folder.iterdir()
    if item.name not in _SKIP
  )


def _values(name: str) -> dict[str, str]:
  return {"name": name, "command": name, "function": name.replace("-", "_")}


# What the project has ----------------------------------------------------------


@dataclass
class Installed:
  """One added package, as of the last add or upgrade."""

  package: str
  path: str
  """The folder, relative to the project root."""
  version: str
  source: str = BUILTIN
  """Where the package came from: `builtin`, a `[sources]` name, or a folder."""
  vars: dict[str, str] = field(default_factory=dict)
  files: dict[str, str] = field(default_factory=dict)
  """Hash of each file as Micro last gave it to you, by path in the folder."""


class Lock:
  def __init__(self, path: Path, entries: dict[str, Installed]) -> None:
    self.path = path
    self.entries = entries

  @classmethod
  def load(cls, project: Project) -> Lock:
    path = project.root / LOCK
    entries: dict[str, Installed] = {}
    if path.is_file():
      for key, table in tomllib.loads(path.read_text()).items():
        entries[key] = Installed(
          package=table["package"],
          path=table["path"],
          version=table.get("version", "unknown"),
          source=table.get("source", BUILTIN),
          vars=dict(table.get("vars", {})),
          files=dict(table.get("files", {})),
        )
    return cls(path, entries)

  def save(self) -> None:
    if not self.entries:
      self.path.unlink(missing_ok=True)
      return
    quote = json.dumps  # a JSON string is a valid TOML basic string
    lines = [
      "# Written by `micro pkg`; commit it. It records each package file as Micro gave it",
      "# to you, which is how `micro pkg upgrade` tells your edits from Micro's changes.",
      "",
    ]
    for key in sorted(self.entries):
      entry = self.entries[key]
      lines += [
        f"[{key}]",
        f"package = {quote(entry.package)}",
        f"source = {quote(entry.source)}",
        f"path = {quote(entry.path)}",
        f"version = {quote(entry.version)}",
        "",
      ]
      if entry.vars:
        lines += [
          f"[{key}.vars]",
          *(f"{k} = {quote(v)}" for k, v in sorted(entry.vars.items())),
          "",
        ]
      lines += [
        f"[{key}.files]",
        *(f"{quote(f)} = {quote(h)}" for f, h in sorted(entry.files.items())),
        "",
      ]
    self.path.write_text("\n".join(lines))


def _key(name: str) -> str:
  if _NAME.fullmatch(name) is None:
    raise ValueError("Package names use lowercase letters, digits, and hyphens.")
  return name.replace("-", "_")


def add(
  package: str,
  project: Project,
  *,
  name: str | None = None,
  source: str | None = None,
) -> Path:
  """Copy a package from a source (default: builtin) into the project's services."""
  label, root = resolve(project, source)
  shipped = available(root)
  if package not in shipped:
    raise ValueError(
      f"No package {package!r} in the {label} source; choose from: {', '.join(shipped)}."
    )
  templated = _templated(root / package)
  if templated and name is None:
    raise ValueError(
      f"{package!r} is a template: give the copy a name, "
      f"as in `micro pkg add {package} tickets`."
    )
  installed_as = name or package
  key = _key(installed_as)
  folder = project.services / key
  lock = Lock.load(project)
  if (
    key in lock.entries or folder.exists() or (project.services / f"{key}.py").exists()
  ):
    raise FileExistsError(f"{folder} already exists.")
  values = _values(installed_as) if templated else {}
  files = _files(root / package, values)
  for relative, data in files.items():
    target = folder / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
  lock.entries[key] = Installed(
    package=package,
    path=folder.relative_to(project.root).as_posix(),
    version=_version(),
    source=label,
    vars=values,
    files={relative: _hash(data) for relative, data in files.items()},
  )
  lock.save()
  return folder


# Comparing ---------------------------------------------------------------------


@dataclass(frozen=True)
class Change:
  file: str
  kind: Kind


@dataclass
class Report:
  name: str
  package: str
  path: str
  changes: list[Change]
  shipped: bool = True
  """Whether the source still has the package."""
  source: str = BUILTIN
  problem: str | None = None
  """Why the package could not be compared, such as a missing source folder."""

  @property
  def pending(self) -> list[Change]:
    return [c for c in self.changes if c.kind in PENDING]

  @property
  def attention(self) -> list[Change]:
    return [c for c in self.changes if c.kind in ATTENTION]

  @property
  def edited(self) -> list[Change]:
    return [c for c in self.changes if c.kind in ("modified", "deleted")]


def classify(base: str | None, mine: str | None, new: str | None) -> Kind:
  """What to do with one file, from its three hashes (None: absent)."""
  if new is None:  # Micro no longer ships it
    if mine is None:
      return "dropped"
    return "remove" if mine == base else "orphan"
  if base is None:  # Micro ships a new file
    if mine is None:
      return "add"
    return "refresh" if mine == new else "conflict"
  if mine is None:  # you deleted it
    return "deleted" if new == base else "gone"
  if mine == new:
    return "current" if base == new else "refresh"
  if mine == base:
    return "upgrade"
  return "modified" if new == base else "conflict"


def _compare(project: Project, entry: Installed) -> tuple[Report, dict[str, bytes]]:
  name = Path(entry.path).name
  try:
    _, root = resolve(project, entry.source)
  except (FileNotFoundError, ValueError) as error:
    return Report(
      name, entry.package, entry.path, [], False, entry.source, str(error)
    ), {}
  shipped = available(root)
  if entry.package not in shipped:
    return Report(name, entry.package, entry.path, [], False, entry.source), {}
  files = _files(root / entry.package, entry.vars)
  folder = project.root / entry.path
  changes = []
  for relative in sorted(files.keys() | entry.files.keys()):
    path = folder / relative
    mine = _hash(path.read_bytes()) if path.is_file() else None
    new = _hash(files[relative]) if relative in files else None
    changes.append(Change(relative, classify(entry.files.get(relative), mine, new)))
  return Report(name, entry.package, entry.path, changes, source=entry.source), files


def _select(lock: Lock, names: list[str] | None) -> list[str]:
  if not names:
    return sorted(lock.entries)
  chosen = [_key(n) for n in names]
  missing = [n for n in chosen if n not in lock.entries]
  if missing:
    raise ValueError(
      f"Not an added package: {', '.join(missing)}. See `micro pkg status`."
    )
  return chosen


def status(project: Project, names: list[str] | None = None) -> list[Report]:
  """Each added package compared with its source."""
  lock = Lock.load(project)
  return [_compare(project, lock.entries[key])[0] for key in _select(lock, names)]


def diff(project: Project, name: str) -> str:
  """A unified diff of the package's files: yours against its source's."""
  lock = Lock.load(project)
  (key,) = _select(lock, [name])
  entry = lock.entries[key]
  report, files = _compare(project, entry)
  if report.problem:
    raise FileNotFoundError(report.problem)
  folder = project.root / entry.path
  out: list[str] = []
  for change in report.changes:
    if change.kind == "current":
      continue
    path = folder / change.file
    mine = (
      path.read_text(errors="replace").splitlines(keepends=True)
      if path.is_file()
      else []
    )
    new = (
      files[change.file].decode(errors="replace").splitlines(keepends=True)
      if change.file in files
      else []
    )
    if mine != new:
      out += difflib.unified_diff(
        mine,
        new,
        fromfile=f"{entry.path}/{change.file} (yours)",
        tofile=f"{entry.path}/{change.file} ({entry.source})",
      )
  return "".join(out)


def upgrade(
  project: Project,
  names: list[str] | None = None,
  *,
  settle: Literal["theirs", "mine"] | None = None,
) -> list[Report]:
  """Bring packages up to what their sources ship, keeping what you changed.

  Files you never touched are replaced, added, or removed. Files you edited that
  Micro did not change stay. A file both of you changed is a conflict and is left
  alone unless `settle` says: "theirs" writes Micro's, "mine" keeps yours and
  records Micro's as reviewed, so it is not raised again until Micro changes it.
  """
  lock = Lock.load(project)
  reports: list[Report] = []
  for key in _select(lock, names):
    entry = lock.entries[key]
    report, files = _compare(project, entry)
    folder = project.root / entry.path
    outcome: list[Change] = []
    for change in report.changes:
      path = folder / change.file
      kind, settled = change.kind, None
      if kind in ATTENTION and settle is not None:
        settled = settle
        kind = "upgrade" if settle == "theirs" else "refresh"
      if kind in ("upgrade", "add"):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(files[change.file])
        entry.files[change.file] = _hash(files[change.file])
      elif kind == "refresh":
        entry.files[change.file] = _hash(files[change.file])
      elif kind == "remove":
        path.unlink()
        _prune(path.parent, folder)
        del entry.files[change.file]
      elif kind in ("orphan", "dropped"):
        del entry.files[change.file]
      outcome.append(Change(change.file, settled or change.kind))
    report.changes = outcome
    if (
      any(c.kind in PENDING or c.kind in ("theirs", "mine") for c in outcome)
      and not report.attention
    ):
      entry.version = _version()
    reports.append(report)
  lock.save()
  return reports


def _prune(folder: Path, stop: Path) -> None:
  while folder != stop and folder.is_dir() and not any(folder.iterdir()):
    folder.rmdir()
    folder = folder.parent


def forget(project: Project, name: str) -> None:
  """Stop tracking a package; its files stay where they are."""
  lock = Lock.load(project)
  (key,) = _select(lock, [name])
  del lock.entries[key]
  lock.save()
