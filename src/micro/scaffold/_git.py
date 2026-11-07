"""The little of git that packages need: find a commit, read a folder at it, merge.

Everything runs the `git` binary. Nothing is cloned for good: a folder is read at
one commit into a temporary repository and deleted, so there is no cache to
manage. Prompts are turned off, so a missing credential fails instead of waiting.
"""

import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

_COMMIT = re.compile(r"[0-9a-f]{40}")


class GitError(ConnectionError):
  """git is missing or a git command failed."""


def _env() -> dict[str, str]:
  env = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "LC_ALL": "C"}
  # An ssh key with a passphrase or an unknown host would otherwise wait for a person.
  env.setdefault("GIT_SSH_COMMAND", "ssh -o BatchMode=yes")
  return env


def git(*args: str, cwd: Path | None = None, ok: tuple[int, ...] = (0,)) -> str:
  if shutil.which("git") is None:
    raise GitError(
      "`micro pkg` needs git to fetch packages; install it (for example "
      "`brew install git` or `apt install git`)."
    )
  done = subprocess.run(
    ["git", *args], cwd=cwd, env=_env(), capture_output=True, text=True, check=False
  )
  if done.returncode not in ok:
    detail = (done.stderr or done.stdout).strip().splitlines()
    raise GitError(f"git {args[0]} failed: {detail[-1] if detail else done.returncode}")
  return done.stdout


_HTTPS = re.compile(r"https://(?:[^/@]+@)?(?P<host>[^/:]+)/(?P<path>.+?)(?:\.git)?/?")
_SSH = re.compile(
  r"(?:git@(?P<scp_host>[^/:]+):|ssh://git@(?P<url_host>[^/:]+)/)(?P<path>.+?)(?:\.git)?/?"
)
_connected: dict[str, str] = {}


def remotes(url: str) -> list[str]:
  """The ways to reach one repository: HTTPS and SSH, the one given first.

  `https://host/owner/repo` and `git@host:owner/repo` name the same repository on
  GitHub, GitLab, Codeberg and most hosts, so either works on a machine that has
  the matching credentials. Other URLs (`file://`, a local path) stand alone.
  """
  if found := _HTTPS.fullmatch(url):
    return [url, f"git@{found['host']}:{found['path']}.git"]
  if found := _SSH.fullmatch(url):
    host = found["scp_host"] or found["url_host"]
    return [url, f"https://{host}/{found['path']}.git"]
  return [url]


def connect(url: str) -> str:
  """The first of a repository's remotes that answers (remembered for this run)."""
  if url in _connected:
    return _connected[url]
  last: GitError | None = None
  for candidate in remotes(url):
    try:
      git("ls-remote", "--exit-code", candidate, "HEAD")
    except GitError as error:
      last = error
      continue
    _connected[url] = candidate
    return candidate
  raise GitError(f"Cannot reach {url}" + (f": {last}" if last else "."))


def is_commit(ref: str) -> bool:
  return _COMMIT.fullmatch(ref) is not None


def default_branch(url: str) -> tuple[str, str]:
  """The branch a remote's HEAD points at, and its commit."""
  out = git("ls-remote", "--symref", url, "HEAD")
  branch = ""
  for line in out.splitlines():
    if line.startswith("ref: "):
      branch = line.split()[1].removeprefix("refs/heads/")
    elif line.endswith("\tHEAD"):
      commit = line.split()[0]
      return branch or "HEAD", commit
  raise GitError(f"{url} has no HEAD.")


def resolve(url: str, ref: str) -> str:
  """The commit a branch, tag or commit hash points at."""
  if is_commit(ref):
    return ref
  out = git(
    "ls-remote", url, ref, f"refs/tags/{ref}", f"refs/heads/{ref}", f"{ref}^{{}}"
  )
  commits: dict[str, str] = {}
  for line in out.splitlines():
    commit, _, name = line.partition("\t")
    commits[name] = commit
  # An annotated tag lists its own object and, as `^{}`, the commit it tags.
  for name in (f"refs/tags/{ref}^{{}}", f"refs/tags/{ref}", f"refs/heads/{ref}", ref):
    if name in commits:
      return commits[name]
  raise GitError(f"{url} has no branch, tag or commit {ref!r}.")


def read_folder(url: str, commit: str, path: str) -> dict[str, bytes]:
  """Every file under `path` (a folder in the repository) at `commit`."""
  with tempfile.TemporaryDirectory(prefix="micro-pkg-") as raw:
    repo = Path(raw)
    git("init", "-q", cwd=repo)
    git("remote", "add", "origin", url, cwd=repo)
    # Without history or file contents; the checkout below fetches only what it reads.
    try:
      git(
        "fetch", "-q", "--depth", "1", "--filter=blob:none", "origin", commit, cwd=repo
      )
    except GitError:
      # A server that will not serve a bare commit: fetch everything it has.
      git("fetch", "-q", "origin", cwd=repo)
    wanted = path.strip("/") or "."
    git("checkout", "-q", commit, "--", wanted, cwd=repo)
    root = repo / wanted if wanted != "." else repo
    found: dict[str, bytes] = {}
    if root.is_dir():
      for item in sorted(root.rglob("*")):
        if item.is_file() and ".git" not in item.relative_to(repo).parts[:1]:
          found[item.relative_to(root).as_posix()] = item.read_bytes()
    return found


def merge(
  mine: bytes, base: bytes, theirs: bytes, labels: tuple[str, str]
) -> tuple[bytes, int]:
  """Three-way line merge: your file, the original, the new one.

  Returns the merged bytes and the number of conflicts, left as markers.
  """
  with tempfile.TemporaryDirectory(prefix="micro-merge-") as raw:
    folder = Path(raw)
    files = {"mine": mine, "base": base, "theirs": theirs}
    for name, data in files.items():
      (folder / name).write_bytes(data)
    done = subprocess.run(
      [
        "git",
        "merge-file",
        "-p",
        "-L",
        labels[0],
        "-L",
        "original",
        "-L",
        labels[1],
        "mine",
        "base",
        "theirs",
      ],
      cwd=folder,
      env=_env(),
      capture_output=True,
      check=False,
    )
  if done.returncode < 0 or done.returncode > 127:
    raise GitError("git merge-file failed.")
  return done.stdout, done.returncode
