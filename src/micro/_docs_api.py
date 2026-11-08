"""Documentation generated from the code: the `api` directive and cross-reference roles.

    .. api::
       micro.service.Service
       micro.service.Client brief

renders each object's signature, docstring, and (for classes) every public member with
its own docstring, so reference pages cannot drift from the code. `brief` leaves the
members out. Every object gets an anchor, and `:class:`Service``, `:meth:`Service.listen``,
`:func:`reply_to``, `:attr:`Timer.at`` and `:data:`DEFAULT_NATS_URL`` link to it.
"""

import annotationlib
import dataclasses
import importlib
import inspect
import re
from collections.abc import Iterator
from typing import Any, TypeAliasType

from docutils import nodes
from docutils.parsers.rst import Directive
from docutils.statemachine import StringList

type Registry = dict[str, tuple[str, str]]
"""Dotted name → (page, anchor), for every documented object and member."""

_registry: Registry = {}


def anchor(name: str) -> str:
  """The HTML id docutils gives a hyperlink target called `name`."""
  return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def locate(dotted: str) -> object:
  """Import a dotted name: the longest importable module prefix, then attributes."""
  parts = dotted.split(".")
  for count in range(len(parts), 0, -1):
    try:
      value: object = importlib.import_module(".".join(parts[:count]))
    except ImportError:
      continue
    try:
      for part in parts[count:]:
        value = getattr(value, part)
    except AttributeError:
      continue
    return value
  raise LookupError(f"Cannot import {dotted!r}.")


def members(cls: type) -> Iterator[tuple[str, object]]:
  """Public members a class defines itself, in definition order."""
  for name, value in vars(cls).items():
    if name.startswith("_") or name in {"model_config", "model_fields"}:
      continue
    raw = value.__func__ if isinstance(value, classmethod | staticmethod) else value
    if inspect.isfunction(raw) or isinstance(raw, property):
      yield name, value


def _signature(value: object) -> str:
  """`(a: int, *, b: str = 'x') -> None`, with annotations as written."""
  target = value.fget if isinstance(value, property) else value
  if isinstance(target, classmethod | staticmethod):
    target = target.__func__
  try:
    signature = inspect.signature(
      target,  # type: ignore[arg-type]
      annotation_format=annotationlib.Format.STRING,
    )
  except TypeError, ValueError:
    return "(...)"
  shown: list[str] = []
  star = False
  for index, parameter in enumerate(signature.parameters.values()):
    if index == 0 and parameter.name in {"self", "cls"}:
      continue
    text = parameter.name
    if parameter.kind is parameter.VAR_POSITIONAL:
      text, star = "*" + text, True
    elif parameter.kind is parameter.VAR_KEYWORD:
      text = "**" + text
    elif parameter.kind is parameter.KEYWORD_ONLY and not star:
      shown.append("*")
      star = True
    if parameter.annotation is not parameter.empty:
      text += f": {parameter.annotation}"
    if parameter.default is not parameter.empty:
      default = repr(parameter.default)
      text += (" = " if parameter.annotation is not parameter.empty else "=") + (
        default if len(default) < 40 else "..."
      )
    shown.append(text)
  returns = signature.return_annotation
  suffix = "" if returns is inspect.Signature.empty else f" -> {returns}"
  return f"({', '.join(shown)}){suffix}"


def _docstring(value: object) -> str:
  target = value.fget if isinstance(value, property) else value
  text = inspect.getdoc(target) or ""  # type: ignore[arg-type]
  # Single backticks are code in docstrings; ReST wants two.
  text = re.sub(
    r"(?<![`:\w])`([^`\n]+)`(?!`)(\w?)",
    lambda m: f"``{m.group(1)}``" + ("\\ " + m.group(2) if m.group(2) else ""),
    text,
  )
  out: list[str] = []
  lines = text.splitlines()
  index = 0
  while index < len(lines):
    line = lines[index]
    if line.startswith("    ") and out and out[-1] == "":
      block = []
      while index < len(lines) and (
        lines[index].startswith("    ") or not lines[index]
      ):
        block.append(lines[index])
        index += 1
      while block and not block[-1]:
        block.pop()
      out += [".. code-block:: python", ""] + [
        "   " + b[4:] if b else "" for b in block
      ]
      out.append("")
      continue
    out.append(line)
    index += 1
  return "\n".join(out)


def _indent(text: str, by: str) -> list[str]:
  return [by + line if line else "" for line in text.splitlines()]


def _kind(value: object) -> str:
  if inspect.isclass(value):
    return "class"
  target = value
  if isinstance(target, classmethod | staticmethod):
    target = target.__func__
  if isinstance(target, property):
    return "property"
  if inspect.iscoroutinefunction(target):
    return "async def"
  return "def"


def fields_of(cls: type) -> list[tuple[str, str]]:
  """Documented data fields of a dataclass or Pydantic model: (name, type)."""
  found: list[tuple[str, str]] = []
  if dataclasses.is_dataclass(cls):
    found = [
      (f.name, str(f.type))
      for f in dataclasses.fields(cls)
      if not f.name.startswith("_")
    ]
  elif hasattr(cls, "model_fields"):
    found = [
      (name, getattr(info.annotation, "__name__", str(info.annotation)))
      for name, info in cls.model_fields.items()  # type: ignore[attr-defined]
      if not name.startswith("_")
    ]
  return found


def entries(dotted: str, brief: bool) -> list[tuple[str, str, object]]:
  """`(dotted name, short name, object)` for an object and its members."""
  value = locate(dotted)
  result: list[tuple[str, str, object]] = [(dotted, dotted.rpartition(".")[2], value)]
  if inspect.isclass(value) and not brief:
    for name, member in members(value):
      result.append((f"{dotted}.{name}", name, member))
  return result


def render(dotted: str, brief: bool) -> list[str]:
  """ReST for one documented object."""
  items = entries(dotted, brief)
  value = locate(dotted)
  lines = [f".. _{dotted}:", ""]
  short = dotted.rpartition(".")[2]
  if isinstance(value, TypeAliasType):
    lines += [f"**type** ``{short}`` = ``{value.__value__}``", ""]
  elif inspect.isclass(value):
    lines += [f"**class** ``{short}{_signature(value)}``", ""]
  elif callable(value):
    kind = "async def" if inspect.iscoroutinefunction(value) else "def"
    lines += [f"**{kind}** ``{short}{_signature(value)}``", ""]
  else:
    shown = repr(value)
    if len(shown) > 60 or " at 0x" in shown or "``" in shown:
      shown = f"<{type(value).__name__}>"
    lines += [f"**{short}** = ``{shown}``", ""]
  doc = (
    _docstring(value)
    if (callable(value) or inspect.isclass(value))
    and not isinstance(value, TypeAliasType)
    else ""
  )
  if not doc and not inspect.isclass(value):
    doc = ""
  lines += _indent(doc, "") + [""] if doc else []
  if inspect.isclass(value) and not brief:
    own = fields_of(value)
    if own:
      lines += ["Fields: " + ", ".join(f"``{n}``" for n, _ in own), ""]
    for full, name, member in items[1:]:
      kind = _kind(member)
      shown = f"``{name}``" if kind == "property" else f"``{name}{_signature(member)}``"
      label = "" if kind == "property" else f"{kind} "
      lines += [f".. _{full}:", "", f"{label}{shown}".strip()]
      body = _docstring(member) or "(no description)"
      lines += _indent(body, "    ") + [""]
  return lines


class ApiDirective(Directive):
  has_content = True

  def run(self) -> list[nodes.Node]:
    lines: list[str] = []
    for entry in (line.strip() for line in self.content):
      if not entry:
        continue
      dotted, _, flag = entry.partition(" ")
      try:
        lines += render(dotted, flag.strip() == "brief")
      except LookupError as error:
        raise self.error(str(error)) from error
    container = nodes.Element()
    self.state.nested_parse(StringList(lines), self.content_offset, container)
    return list(container.children)


def register(page: str, source: str) -> None:
  """Record where each `api` entry of a page lives, for the roles to link to."""
  for block in re.finditer(r"^\.\. api::\n((?:[ \t]+.*\n?|\n)*)", source, re.MULTILINE):
    for line in block.group(1).splitlines():
      entry = line.strip()
      if not entry:
        continue
      dotted, _, flag = entry.partition(" ")
      try:
        for full, _short, _value in entries(dotted, flag.strip() == "brief"):
          _registry[full] = (page, anchor(full))
      except LookupError:
        continue


def reset() -> None:
  _registry.clear()


def lookup(name: str) -> tuple[str, str] | None:
  """Find a documented object by full dotted name or by its trailing part."""
  if name in _registry:
    return _registry[name]
  matches = [key for key in _registry if key == name or key.endswith("." + name)]
  if len(matches) == 1:
    return _registry[matches[0]]
  # Prefer the shortest when several modules re-document one name.
  return _registry[min(matches, key=len)] if matches else None


def documented() -> set[str]:
  return set(_registry)


def role(
  name: str,
  rawtext: str,
  text: str,
  lineno: int,
  inliner: Any,
  options: Any = None,
  content: Any = None,
) -> tuple[list[nodes.Node], list[nodes.system_message]]:
  match = re.fullmatch(r"(.*?)\s*<([^>]+)>", text)
  label, target = (match.group(1), match.group(2)) if match else (None, text)
  shown = label or target.lstrip("~").rpartition(".")[2] or target
  found = lookup(target.lstrip("~"))
  literal = nodes.literal(rawtext, shown)
  if found is None:
    message = inliner.reporter.warning(
      f"No documented object {target!r} for :{name}:", line=lineno
    )
    return [literal], [message]
  page, ident = found
  return [nodes.reference(rawtext, "", literal, refuri=f"{page}.html#{ident}")], []


PUBLIC_MODULES = (
  "micro.runtime",
  "micro.coordination",
  "micro.config",
  "micro.service",
  "micro.errors",
  "micro.scheduler",
  "micro.gateway",
  "micro.discord",
  "micro.discord.interactions",
  "micro.discord.filters",
  "micro.discord.messages",
  "micro.discord.refs",
  "micro.discord.ui",
  "micro.discord.colour",
  "micro.discord.objects",
  "micro.discord.state",
  "micro.discord.invite",
  "micro.middleware",
  "micro.http",
  "micro.store",
)
"""Modules whose public names must each have a reference entry."""


def public_names(module: str) -> list[str]:
  """What a module exports: its `__all__`, else the names it defines itself."""
  target = importlib.import_module(module)
  exported = getattr(target, "__all__", None)
  if exported is not None:
    names = [name for name in exported if not name.startswith("_")]
  else:
    names = [
      name
      for name, value in vars(target).items()
      if not name.startswith("_")
      and (inspect.isclass(value) or inspect.isfunction(value))
      and getattr(value, "__module__", None) == module
    ]
  return names


def missing_entries() -> list[str]:
  """Public names with no reference entry anywhere in the docs (modules are skipped)."""
  documented_ids: set[int] = set()
  for full in _registry:
    try:
      documented_ids.add(id(locate(full)))
    except LookupError:
      continue
  missing: list[str] = []
  for module in PUBLIC_MODULES:
    target = importlib.import_module(module)
    for name in public_names(module):
      value = getattr(target, name, None)
      if value is None or inspect.ismodule(value):
        continue
      if id(value) not in documented_ids and f"{module}.{name}" not in _registry:
        missing.append(f"{module}.{name}")
  return missing


def missing_descriptions() -> list[str]:
  """Documented classes, functions and members that have no docstring."""
  gaps: list[str] = []
  for full in sorted(_registry):
    try:
      value = locate(full)
    except LookupError:
      continue
    if isinstance(value, str | int | float | tuple | frozenset | dict):
      continue
    if isinstance(value, property):
      text = inspect.getdoc(value.fget) if value.fget else None
    else:
      text = inspect.getdoc(value)
      if inspect.isclass(value) and text == inspect.getdoc(object):
        text = None
    if not text or (inspect.isclass(value) and text.startswith(f"{value.__name__}(")):
      gaps.append(full)
  return gaps
