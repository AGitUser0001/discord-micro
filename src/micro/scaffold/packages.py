"""Packages: services you copy into your project from a source, then own.

A package comes from a source: a git repository (or a folder) named in micro.toml;
`builtin` is Micro's own examples. `add` copies a package into the project's
services, and `micro.lock` records where it came from (source, ref, the exact
commit) and the hash of every file as it was copied. The files are yours to edit.
`upgrade` fetches what the package's ref points at now and, per file, compares the
recorded hash (what the source last gave you), the file now, and the new version:

* a file you never touched is replaced, added or removed;
* a file only you changed stays;
* a file both of you changed is merged line by line against the commit you
  installed (git's three-way merge); overlapping edits are left as conflict markers.

    micro pkg add builtin/chat         # services/chat/
    micro pkg add team/billing         # a package from another source
    micro pkg status                   # what an upgrade would change
    micro pkg upgrade                  # apply it, keeping your edits
"""

import difflib
import hashlib
import json
import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from string import Template
from typing import TYPE_CHECKING, Literal

from . import _git, _sources
from ._sources import BUILTIN, Resolved, Source

if TYPE_CHECKING:
  from . import Project

LOCK = "micro.lock"
"""The file, beside micro.toml, recording the packages added to the project."""

_NAME = re.compile(r"[a-z][a-z0-9-]*[a-z0-9]|[a-z]")
_MARKERS = re.compile(rb"^<{7} .*$", re.MULTILINE)
_UNREADABLE = (_git.GitError, FileNotFoundError, ValueError)
FETCH_ERRORS = _git.GitError
"""What a package fetch raises when git is missing or a source cannot be reached."""

type Kind = Literal[
  "current",  # your file is what the source ships
  "refresh",  # same content already; only the record is stale
  "upgrade",  # you never touched it and the source changed it
  "add",  # the source ships a new file
  "remove",  # the source dropped a file you never touched
  "orphan",  # the source dropped a file you edited: kept
  "dropped",  # the source dropped a file you had already deleted
  "modified",  # you edited it and the source did not change it
  "deleted",  # you deleted it and the source did not change it
  "conflict",  # you and the source both changed it (no original to merge with)
  "gone",  # you deleted it and the source changed it
  "markers",  # merged with overlapping edits: resolve the markers
  "merged",  # you and the source both changed it, merged cleanly
  "theirs",  # a conflict settled with the source's version
  "mine",  # a conflict settled by keeping yours
]
ATTENTION: frozenset[Kind] = frozenset({"conflict", "gone", "markers"})
"""Kinds that need a decision: edit the markers, or `--theirs` / `--mine`."""
PENDING: frozenset[Kind] = frozenset(
  {"upgrade", "add", "remove", "refresh", "orphan", "dropped"}
)
"""Kinds `upgrade` applies on its own."""


def _version() -> str:
  from importlib.metadata import PackageNotFoundError, version

  try:
    return version("discord-micro")
  except PackageNotFoundError:
    return "unknown"


def _hash(data: bytes) -> str:
  return "sha256:" + hashlib.sha256(data).hexdigest()


# What a source ships ---------------------------------------------------------------


def describe(files: dict[str, bytes]) -> str:
  """A package's one-line description: package.toml's, else its docstring's."""
  if "package.toml" in files:
    text = tomllib.loads(files["package.toml"].decode()).get("description")
    if isinstance(text, str):
      return text
  init = files.get("__init__.py", b"").decode(errors="replace")
  if init.startswith('"""'):
    return init.split('"""')[1].strip().splitlines()[0]
  return ""


@dataclass
class Listing:
  source: Source
  resolved: Resolved | None = None
  packages: dict[str, str] = field(default_factory=dict)
  """Package names and one-line descriptions."""
  problem: str | None = None


def listing(root: Path, only: str | None = None) -> list[Listing]:
  """The packages in each source (or just `only`), as they are now."""
  sources = _sources.configured(root)
  chosen = [_sources.find(root, only)] if only else list(sources.values())
  found: list[Listing] = []
  for source in chosen:
    try:
      resolved = _sources.resolve(source)
      shipped = _sources.packages_in(_sources.tree(source, resolved.commit, root))
      found.append(
        Listing(source, resolved, {n: describe(f) for n, f in sorted(shipped.items())})
      )
    except _UNREADABLE as error:
      found.append(Listing(source, problem=str(error)))
  return found


def _render(files: dict[str, bytes], values: dict[str, str]) -> dict[str, bytes]:
  """A package's files as they would be written: `.tmpl` files filled in."""
  found: dict[str, bytes] = {}
  for name, data in sorted(files.items()):
    if name == "package.toml" or "__pycache__" in name.split("/"):
      continue
    if name.endswith(".tmpl"):
      data = Template(data.decode()).substitute(values).encode()
      name = name.removesuffix(".tmpl")
    found[name] = data
  return found


def _templated(files: dict[str, bytes]) -> bool:
  return any(name.endswith(".tmpl") for name in files)


def _values(name: str) -> dict[str, str]:
  return {"name": name, "command": name, "function": name.replace("-", "_")}


class _Fetched:
  """What one command has already asked a source, so each is fetched once."""

  def __init__(self, project: Project) -> None:
    self.project = project
    self._tips: dict[tuple[str, str | None], Resolved] = {}
    self._packages: dict[tuple[str, str], dict[str, dict[str, bytes]]] = {}

  def source(self, entry: Installed) -> Source:
    named = _sources.configured(self.project.root).get(entry.source)
    if named is not None:
      return named
    if entry.source == BUILTIN or not (entry.url or entry.root):
      return _sources.builtin()
    return Source(entry.source, entry.url or None, entry.root or ".")

  def tip(self, source: Source, ref: str | None) -> Resolved:
    key = (source.name, ref)
    if key not in self._tips:
      self._tips[key] = _sources.resolve(source, ref)
    return self._tips[key]

  def packages(self, source: Source, commit: str) -> dict[str, dict[str, bytes]]:
    key = (source.name, commit)
    if key not in self._packages:
      files = _sources.tree(source, commit, self.project.root)
      self._packages[key] = _sources.packages_in(files)
    return self._packages[key]


# What the project has ----------------------------------------------------------


@dataclass
class Installed:
  """One added package, as of the last add or upgrade."""

  package: str
  path: str
  """The folder, relative to the project root."""
  version: str
  source: str = BUILTIN
  """The source's name in micro.toml."""
  url: str = ""
  """Where that source was (empty for a folder), in case micro.toml forgets it."""
  root: str = ""
  """The folder holding packages inside the source."""
  ref: str = ""
  """The branch or tag `upgrade` follows (empty for a folder)."""
  commit: str = ""
  """The exact commit installed: the original that merges are made against."""
  vars: dict[str, str] = field(default_factory=dict)
  files: dict[str, str] = field(default_factory=dict)
  """Hash of each file as the source last gave it to you, by path in the folder."""


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
          url=table.get("url", ""),
          root=table.get("root", ""),
          ref=table.get("ref", ""),
          commit=table.get("commit", ""),
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
      "# Written by `micro pkg`; commit it. It records where each package came from and",
      "# each file as the source gave it to you, which is how `micro pkg upgrade` tells your",
      "# edits from the source's changes.",
      "",
    ]
    for key in sorted(self.entries):
      entry = self.entries[key]
      lines += [
        f"[{key}]",
        f"package = {quote(entry.package)}",
        f"source = {quote(entry.source)}",
        *([f"url = {quote(entry.url)}"] if entry.url else []),
        *([f"root = {quote(entry.root)}"] if entry.root else []),
        *([f"ref = {quote(entry.ref)}"] if entry.ref else []),
        *([f"commit = {quote(entry.commit)}"] if entry.commit else []),
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
  spec: str,
  project: Project,
  *,
  name: str | None = None,
  ref: str | None = None,
) -> Path:
  """Copy a package into the project's services: `SOURCE/NAME`, as in `builtin/chat`."""
  source_name, slash, package = spec.partition("/")
  if not (slash and source_name and package):
    raise ValueError(
      f"Name the source as well: SOURCE/NAME, as in `micro pkg add builtin/{spec.strip('/')}`."
    )
  source = _sources.find(project.root, source_name)
  resolved = _sources.resolve(source, ref)
  shipped = _sources.packages_in(_sources.tree(source, resolved.commit, project.root))
  if package not in shipped:
    raise ValueError(
      f"No package {package!r} in the {source.name} source; "
      f"choose from: {', '.join(shipped) or 'none'}."
    )
  templated = _templated(shipped[package])
  if templated and name is None:
    raise ValueError(
      f"{package!r} is a template: give the copy a name, "
      f"as in `micro pkg add {spec} tickets`."
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
  files = _render(shipped[package], values)
  for relative, data in files.items():
    target = folder / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
  lock.entries[key] = Installed(
    package=package,
    path=folder.relative_to(project.root).as_posix(),
    version=_version(),
    source=source.name,
    url=source.url or "",
    root=source.path,
    ref=resolved.ref,
    commit=resolved.commit,
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
  ref: str = ""
  commit: str = ""
  """What is installed."""
  tip: str = ""
  """What the ref points at now."""
  problem: str | None = None
  """Why the package could not be compared, such as an unreachable source."""

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
  if new is None:  # the source no longer ships it
    if mine is None:
      return "dropped"
    return "remove" if mine == base else "orphan"
  if base is None:  # the source ships a new file
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


def _compare(
  project: Project, entry: Installed, fetched: _Fetched, ref: str | None = None
) -> tuple[Report, dict[str, bytes], Source | None]:
  name = Path(entry.path).name

  def report(**more: object) -> Report:
    return Report(
      name,
      entry.package,
      entry.path,
      [],
      source=entry.source,
      ref=entry.ref,
      commit=entry.commit,
      **more,  # type: ignore[arg-type]
    )

  source = fetched.source(entry)
  try:
    tip = fetched.tip(source, ref if ref is not None else entry.ref or None)
    shipped = fetched.packages(source, tip.commit)
  except _UNREADABLE as error:
    return report(shipped=False, problem=str(error)), {}, None
  if entry.package not in shipped:
    return report(shipped=False, tip=tip.commit), {}, source
  files = _render(shipped[entry.package], entry.vars)
  folder = project.root / entry.path
  changes: list[Change] = []
  for relative in sorted(files.keys() | entry.files.keys()):
    path = folder / relative
    data = path.read_bytes() if path.is_file() else None
    mine = _hash(data) if data is not None else None
    new = _hash(files[relative]) if relative in files else None
    kind = classify(entry.files.get(relative), mine, new)
    if data is not None and _MARKERS.search(data):
      kind = "markers"  # unresolved conflict markers, whatever the hashes say
    changes.append(Change(relative, kind))
  done = report(tip=tip.commit)
  done.changes = changes
  done.ref = tip.ref
  return done, files, source


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
  """Each added package compared with what its source ships now."""
  lock = Lock.load(project)
  fetched = _Fetched(project)
  return [
    _compare(project, lock.entries[key], fetched)[0] for key in _select(lock, names)
  ]


def diff(project: Project, name: str) -> str:
  """A unified diff of the package's files: yours against its source's."""
  lock = Lock.load(project)
  (key,) = _select(lock, [name])
  entry = lock.entries[key]
  report, files, _ = _compare(project, entry, _Fetched(project))
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
  ref: str | None = None,
) -> list[Report]:
  """Bring packages up to what their sources ship, keeping what you changed.

  Files you never touched are replaced, added, or removed. Files you edited that
  the source did not change stay. A file both of you changed is merged against the
  commit you installed: clean merges are written, overlapping edits become conflict
  markers. Without that commit (an older lock) it is a conflict left alone unless
  `settle` says: "theirs" writes the source's, "mine" keeps yours and records the
  source's as reviewed. `ref` moves one package to another branch, tag or commit.
  """
  lock = Lock.load(project)
  keys = _select(lock, names)
  if ref is not None and len(keys) != 1:
    raise ValueError("--ref moves one package: name it.")
  fetched = _Fetched(project)
  reports: list[Report] = []
  for key in keys:
    entry = lock.entries[key]
    report, files, source = _compare(project, entry, fetched, ref)
    if report.problem or source is None or not report.shipped:
      reports.append(report)
      continue
    folder = project.root / entry.path
    original = _original(entry, source, fetched)
    outcome: list[Change] = []
    for change in report.changes:
      path = folder / change.file
      kind, settled = change.kind, None
      if kind in ATTENTION and settle is not None:
        settled = settle
        kind = "upgrade" if settle == "theirs" else "refresh"
        if kind == "upgrade" and change.file not in files:
          kind = "remove" if path.is_file() else "dropped"
      elif kind == "conflict":
        merged = _merge(path, original, entry, files, change.file, source, report)
        if merged is not None:
          outcome.append(Change(change.file, merged))
          continue
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
    # The lock follows the files. What is still undecided stays flagged: merged files
    # already record the new version, and a deletion or a conflict with no original to
    # merge against needs your decision, not the old commit.
    entry.version = _version()
    entry.ref = report.ref
    entry.commit = report.tip or entry.commit
    entry.url = source.url or ""
    entry.root = source.path
    report.commit = entry.commit
    reports.append(report)
  lock.save()
  return reports


def _merge(
  path: Path,
  original: dict[str, bytes],
  entry: Installed,
  files: dict[str, bytes],
  relative: str,
  source: Source,
  report: Report,
) -> Kind | None:
  """Merge a file both of you changed; None if there is no original to merge against."""
  base = original.get(relative)
  if base is None or _hash(base) != entry.files.get(relative):
    return None
  label = f"{source.name}/{entry.package}@{report.tip[:7] or 'new'}"
  merged, conflicts = _git.merge(
    path.read_bytes(), base, files[relative], ("yours", label)
  )
  path.write_bytes(merged)
  entry.files[relative] = _hash(files[relative])
  return "markers" if conflicts else "merged"


def _original(entry: Installed, source: Source, fetched: _Fetched) -> dict[str, bytes]:
  """The package's files as installed: what merges are made against."""
  if not entry.commit:
    return {}
  try:
    shipped = fetched.packages(source, entry.commit)
  except _UNREADABLE:
    return {}
  if entry.package not in shipped:
    return {}
  return _render(shipped[entry.package], entry.vars)


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
