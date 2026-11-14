"""Custom ID routes: a service declares them, the router matches with them.

    components.match("ticket.{action}:{id:\\d+}")        # a template
    components.match(re.compile(r"ticket\\.(?P<action>\\w+):(?P<id>\\d+)"))
    components.match(MyRoute(...))                       # any `Route`

A route is data: it travels in the service's presence entry as `dump()`, and the
router rebuilds it with `load()` (importing its class), so the router needs the
same package a custom route comes from. Never put secrets in `dump()`.
"""

import hashlib
import importlib
import json
import re
from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any, Self, cast

from pydantic import JsonValue

from micro import log

_PLACEHOLDER = re.compile(r"\{(\w+)(?::([^{}]+))?\}")
_META = set(".^$*+?{}[]|()\\")


class Route(ABC):
  """Decides whether a custom ID belongs to a handler, and what it carries."""

  prefix: str = ""
  """A literal every matching ID starts with; the router indexes on it."""

  @abstractmethod
  def match(self, custom_id: str) -> Mapping[str, Any] | None:
    """None if the ID is not this route's; otherwise `ctx.route` (may be empty)."""

  @abstractmethod
  def dump(self) -> JsonValue:
    """What the router needs to rebuild this route (no secrets)."""

  @classmethod
  @abstractmethod
  def load(cls, data: JsonValue) -> Self:
    """Rebuild a route from what `dump()` returned."""
    ...


class PatternRoute(Route):
  """A literal prefix plus an optional regex.

  Without a regex, IDs equal to the prefix or nested under it (`.` or `:`)
  match. With one, the whole ID must match, and its named groups become
  `ctx.route`. The regex should start with the prefix, which is checked first.
  """

  def __init__(self, prefix: str, pattern: str | None = None, flags: int = 0) -> None:
    self.prefix = prefix
    self.pattern = pattern
    self.flags = flags
    self._regex = re.compile(pattern, flags) if pattern is not None else None
    if not prefix and pattern is None:
      raise ValueError("A route needs a prefix or a pattern.")

  @classmethod
  def template(cls, template: str) -> Self:
    """`ticket.{action}:{id}`: `{name}` is one segment, `{name:regex}` your own."""
    pattern: list[str] = []
    position = 0
    for found in _PLACEHOLDER.finditer(template):
      pattern.append(re.escape(template[position : found.start()]))
      name, regex = found.groups()
      pattern.append(f"(?P<{name}>{regex or '[^.:]+'})")
      position = found.end()
    pattern.append(re.escape(template[position:]))
    head = template[: template.find("{")] if "{" in template else template
    return cls(head, "".join(pattern))

  @classmethod
  def compiled(cls, regex: re.Pattern[str], prefix: str | None = None) -> Self:
    """The compiled regex, or None for a prefix-only route."""
    head = literal_head(regex.pattern) if prefix is None else prefix
    return cls(head, regex.pattern, regex.flags)

  def match(self, custom_id: str) -> Mapping[str, Any] | None:
    if not custom_id.startswith(self.prefix):
      return None
    if self._regex is None:
      rest = custom_id[len(self.prefix) :]
      nested = not rest or rest[0] in ".:" or self.prefix[-1] in ".:"
      return {} if nested else None
    found = self._regex.fullmatch(custom_id)
    return found.groupdict() if found else None

  def dump(self) -> JsonValue:
    return {"prefix": self.prefix, "pattern": self.pattern, "flags": self.flags}

  @classmethod
  def load(cls, data: JsonValue) -> Self:
    """Rebuild the route from what `dump()` returned."""
    if not isinstance(data, dict):
      raise TypeError("A pattern route is an object.")
    pattern, flags = data.get("pattern"), data.get("flags", 0)
    return cls(
      str(data.get("prefix", "")),
      pattern if isinstance(pattern, str) else None,
      flags if isinstance(flags, int) else 0,
    )


def literal_head(pattern: str) -> str:
  """The characters a regex must start with (conservative: "" if unsure)."""
  head: list[str] = []
  index = 0
  while index < len(pattern):
    char = pattern[index]
    if char == "^" and index == 0:
      index += 1
      continue
    if char == "\\" and index + 1 < len(pattern):
      following = pattern[index + 1]
      if following.isalnum():  # \d, \w, \1 ...: a class, not a literal
        break
      head.append(following)
      index += 2
      continue
    if char in _META:
      break
    head.append(char)
    index += 1
  # A quantifier on the last literal makes it optional or repeated.
  if index < len(pattern) and pattern[index] in "*+?{" and head:
    head.pop()
  return "".join(head)


def kind_of(route: Route) -> str:
  cls = type(route)
  return f"{cls.__module__}:{cls.__qualname__}"


def wire_of(route: Route) -> dict[str, JsonValue]:
  return {"kind": kind_of(route), "data": route.dump()}


def route_id(route: Route) -> str:
  """A short stable name for a route's queue, from what it dumps."""
  text = json.dumps(wire_of(route), sort_keys=True, separators=(",", ":"))
  return "p-" + hashlib.sha256(text.encode()).hexdigest()[:10]


def load_route(wire: Mapping[str, Any]) -> Route:
  """Rebuild a route from its wire form; raises if its class cannot be imported."""
  kind = wire.get("kind")
  if not isinstance(kind, str) or ":" not in kind:
    raise ValueError(f"Bad route kind {kind!r}.")
  module_name, _, qualname = kind.partition(":")
  target: Any = importlib.import_module(module_name)
  for part in qualname.split("."):
    target = getattr(target, part)
  if not (isinstance(target, type) and issubclass(target, Route)):
    raise TypeError(f"{kind} is not a Route.")
  return cast("type[Route]", target).load(wire.get("data"))


def as_route(route: Route | str | re.Pattern[str], prefix: str | None = None) -> Route:
  if isinstance(route, Route):
    return route
  if isinstance(route, re.Pattern):
    return PatternRoute.compiled(route, prefix)
  if _PLACEHOLDER.search(route):
    return PatternRoute.template(route)
  return PatternRoute(route)


class RouteTable:
  """The router's view of every declared route, indexed by literal prefix."""

  def __init__(self) -> None:
    self._buckets: dict[str, list[tuple[str, Route]]] = {}
    self._lengths: list[int] = []

  @classmethod
  def build(cls, declared: Mapping[str, Mapping[str, Any]]) -> Self:
    """`{queue route: wire}` for every route in the directory."""
    table = cls()
    for queue, wire in sorted(declared.items()):
      try:
        route = load_route(wire)
      except Exception as error:
        _warn_once(queue, f"Cannot load route {wire.get('kind')!r}: {error}")
        continue
      table._buckets.setdefault(route.prefix, []).append((queue, route))
    table._lengths = sorted({len(prefix) for prefix in table._buckets}, reverse=True)
    return table

  def find(self, custom_id: str, scope: str) -> str | None:
    """The queue route for an ID: longest prefix first, then by name.

    `scope` is the queue namespace (`cmp.` or `mdl.`). Several routes matching
    is a mistake in the declarations; it is logged once and the first wins.
    """
    hits: list[str] = []
    for length in self._lengths:
      if length > len(custom_id):
        continue  # the slice would be the whole ID again: one bucket, hit once per length
      for queue, route in self._buckets.get(custom_id[:length], ()):
        if queue.startswith(scope) and route.match(custom_id) is not None:
          hits.append(queue)
    if len(hits) > 1:
      _warn_once(
        ",".join(hits[:2]),
        f"Custom ID {custom_id!r} matches several routes ({', '.join(hits)}); using {hits[0]}.",
      )
    return hits[0] if hits else None

  def __bool__(self) -> bool:
    return bool(self._buckets)


_warned: set[str] = set()


def _warn_once(key: str, message: str) -> None:

  if key not in _warned:
    _warned.add(key)
    log.warning(message)
