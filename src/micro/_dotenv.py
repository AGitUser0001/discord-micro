"""Load the project's `.env` into the environment.

The file sits next to `micro.toml` (or in the current directory without one).
Variables that are already set win, so a real environment always overrides it.
"""

import os
from pathlib import Path


def load(start: Path | None = None) -> Path | None:
  """Set the variables from `.env`; returns the file used, if there is one."""
  here = (start or Path.cwd()).resolve()
  root = next((p for p in (here, *here.parents) if (p / "micro.toml").is_file()), here)
  path = root / ".env"
  if not path.is_file():
    return None
  for line in path.read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if not line or line.startswith("#"):
      continue
    line = line.removeprefix("export ").lstrip()
    name, separator, value = line.partition("=")
    name = name.strip()
    if separator and name.isidentifier():
      os.environ.setdefault(name, _value(value.strip()))
  return path


def _value(raw: str) -> str:
  if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
    inner = raw[1:-1]
    return inner.replace("\\n", "\n") if raw[0] == '"' else inner
  return raw.split(" #", 1)[0].rstrip()
