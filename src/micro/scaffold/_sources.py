"""Where packages come from: git repositories (or a folder), named in micro.toml.

    [sources.builtin]                     # the default; this is what it is without a section
    url = "https://github.com/AGitUser0001/discord-micro.git"
    path = "packages"

    [sources.team]
    url = "git@github.com:acme/bot-packages.git"
    ref = "v2"                            # a branch, tag or commit (default: see `resolve`)

    [sources.local]
    path = "./team-packages"              # no url: a folder on this machine

`micro pkg source add|list|remove` edits these. A source's packages are the folders
inside its `path`.
"""

import json
import os
import re
import tomllib
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from . import _git

BUILTIN = "builtin"
"""The default source: Micro's own examples."""
DEFAULT_URL = "https://github.com/AGitUser0001/discord-micro.git"
DEFAULT_PATH = "packages"
_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]*")
_SKIP = {"__pycache__", "package.toml"}
_trees: dict[tuple[str, str, str], dict[str, bytes]] = {}


@dataclass(frozen=True)
class Source:
  name: str
  url: str | None
  """The git remote, or None for a folder on this machine."""
  path: str
  """The folder holding the packages, inside the repository (or on disk)."""
  ref: str | None = None
  """A branch, tag or commit to follow (default: see `resolve`)."""

  @property
  def where(self) -> str:
    return self.url or self.path


@dataclass(frozen=True)
class Resolved:
  ref: str
  """The branch or tag followed (empty for a folder)."""
  commit: str


def builtin() -> Source:
  return Source(
    BUILTIN, os.environ.get("MICRO_PACKAGES_URL") or DEFAULT_URL, DEFAULT_PATH
  )


def check_name(name: str) -> str:
  if _NAME.fullmatch(name) is None:
    raise ValueError("Source names use letters, digits, hyphens and underscores.")
  return name


def _read(root: Path) -> dict[str, object]:
  path = root / "micro.toml"
  if not path.is_file():
    return {}
  table = tomllib.loads(path.read_text()).get("sources", {})
  return table if isinstance(table, dict) else {}


def configured(root: Path) -> dict[str, Source]:
  """Every source: `builtin` unless micro.toml replaces it, then those it names."""
  found = {BUILTIN: builtin()}
  for name, value in _read(root).items():
    if isinstance(value, str):  # `team = "./folder"`
      found[name] = Source(name, None, value)
    elif isinstance(value, dict):
      url = value.get("url")
      path = value.get("path") or (DEFAULT_PATH if url else ".")
      ref = value.get("ref")
      found[name] = Source(
        name,
        str(url) if url else None,
        str(path),
        str(ref) if ref else None,
      )
  return found


def find(root: Path, name: str) -> Source:
  sources = configured(root)
  if name not in sources:
    raise ValueError(
      f"No package source named {name!r}; known: {', '.join(sorted(sources))}. "
      "Add one with `micro pkg source add NAME URL`."
    )
  return sources[name]


def _micro_version() -> str | None:
  try:
    return version("discord-micro")
  except PackageNotFoundError:
    return None


def resolve(source: Source, ref: str | None = None) -> Resolved:
  """The commit to read. Without a ref: the tag for this Micro's version, else the
  repository's default branch."""
  if source.url is None:
    return Resolved("", "")
  remote = _git.connect(source.url)
  ref = ref or source.ref
  if ref:
    return Resolved(ref, _git.resolve(remote, ref))
  if (current := _micro_version()) is not None:
    tag = f"v{current}"
    try:
      return Resolved(tag, _git.resolve(remote, f"refs/tags/{tag}"))
    except _git.GitError:
      pass
  branch, commit = _git.default_branch(remote)
  return Resolved(branch, commit)


def tree(source: Source, commit: str, root: Path) -> dict[str, bytes]:
  """Every file under the source's path, by path relative to it."""
  if source.url is None:
    folder = Path(source.path).expanduser()
    if not folder.is_absolute():
      folder = root / folder
    if not folder.is_dir():
      raise FileNotFoundError(
        f"Package source {source.name!r}: {folder} is not a folder."
      )
    return {
      item.relative_to(folder).as_posix(): item.read_bytes()
      for item in sorted(folder.rglob("*"))
      if item.is_file()
    }
  key = (source.url, commit, source.path)
  if key not in _trees:
    _trees[key] = _git.read_folder(_git.connect(source.url), commit, source.path)
  return _trees[key]


def packages_in(files: dict[str, bytes]) -> dict[str, dict[str, bytes]]:
  """Group a source's files by package (its first-level folders)."""
  found: dict[str, dict[str, bytes]] = {}
  for relative, data in files.items():
    head, _, rest = relative.partition("/")
    if not rest or head.startswith(("_", ".")) or head in _SKIP:
      continue
    if any(part in _SKIP or part.startswith(".") for part in rest.split("/")[:-1]):
      continue
    found.setdefault(head, {})[rest] = data
  return found


# Editing micro.toml --------------------------------------------------------------


def _section(lines: list[str], name: str) -> tuple[int, int] | None:
  header = f"[sources.{name}]"
  for index, line in enumerate(lines):
    if line.strip() == header:
      end = index + 1
      while end < len(lines) and not lines[end].lstrip().startswith("["):
        end += 1
      return index, end
  return None


def save(root: Path, source: Source) -> None:
  """Write `[sources.NAME]` into micro.toml (replacing it, or appending)."""
  check_name(source.name)
  path = root / "micro.toml"
  lines = path.read_text().splitlines(keepends=True) if path.is_file() else []
  block = [f"[sources.{source.name}]\n"]
  if source.url:
    block.append(f"url = {json.dumps(source.url)}\n")
  block.append(f"path = {json.dumps(source.path)}\n")
  if source.ref:
    block.append(f"ref = {json.dumps(source.ref)}\n")
  found = _section(lines, source.name)
  if found:
    lines[found[0] : found[1]] = [*block, "\n"] if found[1] < len(lines) else block
  else:
    if lines and not lines[-1].endswith("\n"):
      lines[-1] += "\n"
    lines += ["\n", *block] if lines else block
  path.write_text("".join(lines))


def remove(root: Path, name: str) -> None:
  path = root / "micro.toml"
  lines = path.read_text().splitlines(keepends=True) if path.is_file() else []
  found = _section(lines, name)
  if found:
    del lines[found[0] : found[1]]
    while found[0] > 0 and found[0] <= len(lines) and not lines[found[0] - 1].strip():
      del lines[found[0] - 1]
      found = (found[0] - 1, found[1])
    path.write_text("".join(lines))
    return
  old = re.compile(rf"^\s*{re.escape(name)}\s*=")  # the older `[sources]` table form
  kept = [line for line in lines if not old.match(line)]
  if len(kept) == len(lines):
    hint = (
      " (builtin is the default; replace it with `pkg source add builtin …`)"
      if name == BUILTIN
      else ""
    )
    raise ValueError(f"micro.toml has no source named {name!r}{hint}.")
  path.write_text("".join(kept))
