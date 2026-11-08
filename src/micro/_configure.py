"""`micro configure`: a full-screen editor for the shared configuration tables.

Every document in the `micro_config` bucket is listed on the left; the selected one's
fields are on the right. Values are edited in place (booleans toggle, choices cycle, objects
open), written safely against the latest revision, and shown live when another process
changes the table. Documents whose model is known (the Gateway's, or any listed under
`[config]` in micro.toml) are validated before they are written.
"""

import asyncio
import contextlib
import copy
import enum
import importlib
import json
import types
from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated, Any, Literal, Union, get_args, get_origin

from pydantic import BaseModel, ValidationError

from micro._tui import (
  BOLD,
  CYAN,
  DIM,
  GREEN,
  RED,
  REVERSE,
  YELLOW,
  Terminal,
  fit,
  style,
)
from micro.coordination import Table

BUILTIN_MODELS = {"gateway": "micro.gateway:GatewaySettings"}
"""Documents micro itself defines."""

type Message = tuple[str, str]
"""`(kind, text)` with kind `ok`, `error` or `info`."""


@dataclass(slots=True)
class Doc:
  name: str
  model: type[BaseModel] | None
  value: dict[str, Any] | None = None
  """None: the document does not exist yet (a known model can create it)."""
  revision: int | None = None


def load_model(target: str) -> type[BaseModel]:
  module, _, attribute = target.partition(":")
  value: Any = importlib.import_module(module)
  for part in attribute.split("."):
    value = getattr(value, part)
  return value


# Reading a model's field types ---------------------------------------------------------


def _unwrap(annotation: Any) -> Any:
  """Strip Annotated and Optional: `X | None` is X; other unions keep their first model."""
  while get_origin(annotation) is Annotated:
    annotation = get_args(annotation)[0]
  if get_origin(annotation) in (Union, types.UnionType):
    options = [a for a in get_args(annotation) if a is not type(None)]
    models = [a for a in options if isinstance(a, type) and issubclass(a, BaseModel)]
    annotation = models[0] if models else (options[0] if options else None)
    return _unwrap(annotation)
  return annotation


def annotation_at(model: type[BaseModel] | None, path: list[str]) -> Any:
  """The declared type of the field at `path` (None when unknown)."""
  annotation: Any = model
  for part in path:
    annotation = _unwrap(annotation)
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
      info = annotation.model_fields.get(part)
      annotation = info.annotation if info is not None else None
    else:
      return None
  return _unwrap(annotation)


def choices_for(annotation: Any) -> list[Any] | None:
  """The values a field can take when there is a fixed set."""
  if annotation is bool:
    return [False, True]
  if get_origin(annotation) is Literal:
    return list(get_args(annotation))
  if isinstance(annotation, type) and issubclass(annotation, enum.Enum):
    return [member.value for member in annotation]
  return None


def default_object(annotation: Any) -> dict[str, Any] | None:
  """A new nested object for a field that is None but declared as a model."""
  if isinstance(annotation, type) and issubclass(annotation, BaseModel):
    with contextlib.suppress(ValidationError):
      return annotation().model_dump(mode="json")
  return None


# Values -------------------------------------------------------------------------------


def show(value: Any) -> str:
  if value is None:
    return "null"
  if isinstance(value, str):
    return value
  if isinstance(value, dict):
    return (
      "{"
      + ", ".join(f"{k}: {show(v)}" for k, v in list(value.items())[:3])
      + (", …}" if len(value) > 3 else "}")
    )
  if isinstance(value, list):
    return f"[{len(value)} items]"
  return json.dumps(value)


def kind(value: Any) -> str:
  if isinstance(value, bool):
    return "bool"
  return {int: "int", float: "number", str: "text", dict: "object", list: "list"}.get(
    type(value), "null" if value is None else "value"
  )


def parse(text: str, current: Any) -> Any:
  """What was typed: text for text fields, else JSON (falling back to text)."""
  if isinstance(current, str) and not text.startswith('"'):
    return text
  try:
    return json.loads(text)
  except ValueError:
    return text


def _get(root: Any, path: list[str]) -> Any:
  for part in path:
    root = root[int(part)] if isinstance(root, list) else root[part]
  return root


def _set(root: Any, path: list[str], value: Any) -> None:
  parent = _get(root, path[:-1])
  if isinstance(parent, list):
    parent[int(path[-1])] = value
  else:
    parent[path[-1]] = value


# The app ------------------------------------------------------------------------------


class Configure:
  """The editor's state and behavior, independent of the terminal (keys in, lines out)."""

  def __init__(
    self,
    table: Table[Any],
    models: dict[str, type[BaseModel] | None],
    *,
    title: str = "",
    external_editor: Callable[[str], str] | None = None,
  ) -> None:
    self.table = table
    self.models = models
    self.title = title
    self.external_editor = external_editor
    self.docs: dict[str, Doc] = {}
    self.names: list[str] = []
    self.focus: Literal["tables", "fields"] = "tables"
    self.table_cursor = 0
    self.path: list[str] = []
    self.cursor = 0
    self.input: str | None = None
    self._fresh = False
    self.prompt = ""
    self._commit: Callable[[str], Any] | None = None
    self.message: Message = ("info", "")
    self.changed = asyncio.Event()
    self._saved: dict[str, int] = {}

  # Data ---------------------------------------------------------------------------

  async def load(self) -> None:
    stored = await self.table.items()
    docs = {name: Doc(name, model) for name, model in self.models.items()}
    for name, found in stored.items():
      docs[name] = Doc(name, self.models.get(name), found.value, found.revision)
    self.docs = docs
    self.names = sorted(docs)
    self.table_cursor = min(self.table_cursor, max(len(self.names) - 1, 0))

  async def follow(self) -> None:
    """Keep the display current: other processes' changes arrive here."""
    failures = 0
    while True:
      try:
        async for change in self.table.watch(">", lenient=True):
          failures = 0
          if change is None or change.error is not None:
            continue
          doc = self.docs.get(change.key) or Doc(
            change.key, self.models.get(change.key)
          )
          if change.value is None:
            doc.value, doc.revision = None, None
          else:
            doc.value, doc.revision = change.value, change.revision
            if (
              self._saved.get(change.key) != change.revision and change.key in self.docs
            ):
              self.message = (
                "info",
                f"{change.key} was changed elsewhere (revision {change.revision})",
              )
          self.docs[change.key] = doc
          self.names = sorted(self.docs)
          self.changed.set()
      except asyncio.CancelledError:
        raise
      except Exception:
        failures += 1
      await asyncio.sleep(min(2**failures, 30))

  @property
  def doc(self) -> Doc | None:
    return self.docs.get(self.names[self.table_cursor]) if self.names else None

  def container(self) -> Any:
    doc = self.doc
    if doc is None or doc.value is None:
      return None
    try:
      return _get(doc.value, self.path)
    except KeyError, IndexError, ValueError, TypeError:
      self.path = []
      return doc.value

  def rows(self) -> list[tuple[str, Any]]:
    container = self.container()
    if isinstance(container, dict):
      return [(str(k), v) for k, v in container.items()]
    if isinstance(container, list):
      return [(str(i), v) for i, v in enumerate(container)]
    return []

  # Writing ------------------------------------------------------------------------

  async def write(self, change: Callable[[Any], None], summary: str) -> None:
    """Apply `change` to the latest stored document and save it, retrying on conflict."""
    doc = self.doc
    if doc is None:
      return
    while True:
      found = await self.table.get(doc.name)
      if found is None:
        self.message = ("error", f"{doc.name} does not exist yet; press c to create it")
        return
      candidate = copy.deepcopy(found.value)
      try:
        change(candidate)
        if doc.model is not None:
          candidate = doc.model.model_validate(candidate).model_dump(mode="json")
      except ValidationError as error:
        first = error.errors()[0]
        where = ".".join(str(p) for p in first["loc"]) or doc.name
        self.message = ("error", f"{where}: {first['msg']}")
        return
      except (KeyError, IndexError, ValueError, TypeError) as error:
        self.message = ("error", str(error))
        return
      if candidate == found.value:
        self.message = ("info", "unchanged")
        return
      revision = await self.table.update(doc.name, candidate, revision=found.revision)
      if revision is not None:
        doc.value, doc.revision = candidate, revision
        self._saved[doc.name] = revision
        self.message = ("ok", f"saved {summary} (revision {revision})")
        return

  async def set_field(self, path: list[str], value: Any) -> None:
    await self.write(
      lambda root: _set(root, path, value), f"{'.'.join(path)} = {show(value)}"
    )

  async def create(self) -> None:
    doc = self.doc
    if doc is None or doc.value is not None:
      return
    if doc.model is None:
      self.message = (
        "error",
        f"no model is known for {doc.name}, so there are no defaults",
      )
      return
    value = doc.model().model_dump(mode="json")
    revision = await self.table.create(doc.name, value)
    if revision is None:
      await self.load()
      self.message = ("info", f"{doc.name} already existed; loaded it")
      return
    doc.value, doc.revision = value, revision
    self._saved[doc.name] = revision
    self.message = ("ok", f"created {doc.name} with defaults (revision {revision})")

  async def edit_whole(self) -> None:
    doc = self.doc
    if doc is None or doc.value is None or self.external_editor is None:
      return
    found = await self.table.get(doc.name)
    if found is None:
      return
    try:
      edited = json.loads(
        self.external_editor(json.dumps(found.value, indent=2) + "\n")
      )
      if not isinstance(edited, dict):
        raise ValueError("The document must be a JSON object.")  # noqa: TRY004
      if doc.model is not None:
        edited = doc.model.model_validate(edited).model_dump(mode="json")
    except (ValueError, ValidationError) as error:
      self.message = ("error", str(error).splitlines()[0])
      return
    if edited == found.value:
      self.message = ("info", "unchanged")
      return
    revision = await self.table.update(doc.name, edited, revision=found.revision)
    if revision is None:
      self.message = ("error", "it changed while you were editing; nothing was saved")
      return
    doc.value, doc.revision = edited, revision
    self._saved[doc.name] = revision
    self.message = ("ok", f"saved {doc.name} (revision {revision})")

  # Keys ---------------------------------------------------------------------------

  def ask(self, prompt: str, initial: str, commit: Callable[[str], Any]) -> None:
    self.input, self.prompt, self._commit = initial, prompt, commit
    self._fresh = bool(initial)  # the first key typed replaces the current value

  async def handle(self, key: str) -> bool:
    """React to one key; False means quit."""
    if key == "ctrl-c":
      return False
    if self.input is not None:
      return await self._typing(key)
    self.message = ("info", "") if self.message[0] != "error" or key else self.message
    if self.focus == "tables":
      return await self._tables(key)
    return await self._fields(key)

  async def _typing(self, key: str) -> bool:
    assert self.input is not None
    if key == "esc":
      self.input = self._commit = None
    elif key == "enter":
      commit, text = self._commit, self.input
      self.input = self._commit = None
      if commit is not None:
        await commit(text)
    elif key == "backspace":
      self.input, self._fresh = self.input[:-1], False
    elif key == "ctrl-u":
      self.input, self._fresh = "", False
    elif len(key) == 1 and key >= " ":
      self.input = key if self._fresh else self.input + key
      self._fresh = False
    return True

  async def _tables(self, key: str) -> bool:
    if key in {"q", "esc"}:
      return False
    if key in {"up", "k"}:
      self.table_cursor = max(self.table_cursor - 1, 0)
      self.path, self.cursor = [], 0
    elif key in {"down", "j"}:
      self.table_cursor = min(self.table_cursor + 1, max(len(self.names) - 1, 0))
      self.path, self.cursor = [], 0
    elif key in {"enter", "right", "l", "tab"}:
      doc = self.doc
      if doc is not None and doc.value is not None:
        self.focus, self.cursor = "fields", 0
      elif doc is not None:
        self.message = (
          "info",
          "it does not exist yet: press c to create it with defaults",
        )
    elif key == "c":
      await self.create()
    elif key == "r":
      await self.load()
      self.message = ("info", "reloaded")
    elif key == "e":
      await self.edit_whole()
    return True

  async def _fields(self, key: str) -> bool:
    rows = self.rows()
    if key in {"up", "k"}:
      self.cursor = max(self.cursor - 1, 0)
    elif key in {"down", "j"}:
      self.cursor = min(self.cursor + 1, max(len(rows) - 1, 0))
    elif key in {"home"}:
      self.cursor = 0
    elif key in {"end"}:
      self.cursor = max(len(rows) - 1, 0)
    elif key in {"left", "h", "esc", "backspace", "shift-tab"}:
      if self.path:
        self.path.pop()
        self.cursor = 0
      else:
        self.focus = "tables"
    elif key in {"enter", "space", " ", "right", "l"} and rows:
      await self._activate(rows[self.cursor])
    elif key == "d" and rows:
      await self.set_field([*self.path, rows[self.cursor][0]], None)
    elif key == "e":
      await self.edit_whole()
    elif key == "a" and self._can_add():
      self.ask("new key=value: ", "", self._add)
    elif key == "x" and rows and self._can_add():
      name = rows[self.cursor][0]
      await self.write(lambda root: _get(root, self.path).pop(name), f"removed {name}")
      self.cursor = max(self.cursor - 1, 0)
    elif key == "r":
      await self.load()
      self.message = ("info", "reloaded")
    elif key == "q":
      return False
    return True

  def _can_add(self) -> bool:
    doc = self.doc
    if doc is None or not isinstance(self.container(), dict):
      return False
    if doc.model is None:
      return True
    return get_origin(annotation_at(doc.model, self.path)) is dict

  async def _add(self, text: str) -> None:
    key, separator, raw = text.partition("=")
    if not separator or not key.strip():
      self.message = ("error", "type it as key=value")
      return
    path = [*self.path, key.strip()]
    await self.set_field(path, parse(raw, None))

  async def _activate(self, row: tuple[str, Any]) -> None:
    name, value = row
    path = [*self.path, name]
    doc = self.doc
    annotation = annotation_at(doc.model if doc else None, path)
    choices = choices_for(annotation)
    if isinstance(value, dict | list) and value:
      self.path, self.cursor = path, 0
    elif value is None and default_object(annotation) is not None:
      await self.set_field(path, default_object(annotation))
      self.path, self.cursor = path, 0
    elif choices:
      following = (
        choices[(choices.index(value) + 1) % len(choices)]
        if value in choices
        else choices[0]
      )
      await self.set_field(path, following)
    else:

      async def commit(text: str, path: list[str] = path, current: Any = value) -> None:
        await self.set_field(path, parse(text, current))

      self.ask(f"{'.'.join(path)}: ", show(value) if value is not None else "", commit)

  # Drawing ------------------------------------------------------------------------

  def footer(self) -> str:
    if self.input is not None:
      return "enter save · esc cancel · type to replace, backspace to edit"
    if self.focus == "tables":
      return "↑↓ choose · enter open · c create · e edit as text · r reload · q quit"
    extra = " · a add · x remove" if self._can_add() else ""
    return (
      f"↑↓ choose · enter change · ← back · d null{extra} · e edit as text · q quit"
    )

  def render(self, width: int, height: int) -> tuple[list[str], tuple[int, int] | None]:
    width, height = max(width, 40), max(height, 8)
    left = min(max((max((len(n) for n in self.names), default=6)) + 4, 14), 28)
    right = width - left - 1
    lines = [style(fit(f" micro configure  {self.title}", width), REVERSE, BOLD)]
    doc = self.doc
    crumbs = " / ".join(self.path)
    heading = ""
    if doc is not None:
      heading = doc.name + (f" / {crumbs}" if crumbs else "")
      heading += (
        f"   revision {doc.revision}"
        if doc.revision is not None
        else "   (not created)"
      )
      if doc.model is not None:
        heading += f"   {doc.model.__name__}"
    lines.append(
      style(fit(" TABLES", left), DIM) + " " + style(fit(" " + heading, right), BOLD)
    )
    body = height - 4
    tables = self._window(
      [(n, n == (self.doc.name if self.doc else None)) for n in self.names],
      self.table_cursor,
      body,
    )
    rows = self.rows()
    window = self._window([(r, False) for r in rows], self.cursor, body)
    key_width = min(max((len(k) for k, _ in rows), default=4), 24)
    for index in range(body):
      cell = " " * left
      if index < len(tables[0]):
        name, _ = tables[0][index]
        absolute = tables[1] + index
        mark = "▸" if absolute == self.table_cursor else " "
        text = fit(
          f" {mark} {name}" + ("  ○" if self.docs[name].value is None else ""), left
        )
        active = absolute == self.table_cursor
        cell = (
          style(text, REVERSE)
          if active and self.focus == "tables"
          else (style(text, BOLD) if active else text)
        )
      pane = " " * right
      if doc is not None and doc.value is None and index == 0:
        pane = style(
          fit("  not created yet; press c to create it with defaults", right), YELLOW
        )
      elif index < len(window[0]):
        (key, value), _ = window[0][index]
        absolute = window[1] + index
        annotation = annotation_at(doc.model if doc else None, [*self.path, key])
        hint = "←→ cycles" if choices_for(annotation) else kind(value)
        value_width = max(right - key_width - len(hint) - 6, 8)
        text = f"  {fit(key, key_width)}  {fit(show(value), value_width)} {hint}"
        selected = absolute == self.cursor and self.focus == "fields"
        pane = (
          style(fit(text, right), REVERSE)
          if selected
          else (
            fit(text, right)
            if absolute != self.cursor
            else style(fit(text, right), BOLD)
          )
        )
      lines.append(cell + style("│", DIM) + pane)
    kind_, text = self.message
    cursor: tuple[int, int] | None = None
    if self.input is not None:
      line = self.prompt + self.input
      lines.append(style(fit(line, width), CYAN))
      cursor = (len(lines) - 1, min(len(line), width - 1))
    else:
      color = {"ok": GREEN, "error": RED, "info": DIM}[kind_]
      lines.append(style(fit(" " + text, width), color) if text else " " * width)
    lines.append(style(fit(" " + self.footer(), width), DIM))
    return lines, cursor

  @staticmethod
  def _window(items: list[Any], cursor: int, size: int) -> tuple[list[Any], int]:
    if len(items) <= size:
      return items, 0
    start = min(max(cursor - size // 2, 0), len(items) - size)
    return items[start : start + size], start


# Running it ---------------------------------------------------------------------------


async def run(app: Configure, terminal: Terminal) -> None:
  """Drive the editor until the user quits."""
  await app.load()
  follower = asyncio.create_task(app.follow())
  size = terminal.size()

  def paint() -> None:
    lines, cursor = app.render(*terminal.size())
    terminal.draw(lines, cursor)

  paint()
  keys = terminal.keys().__aiter__()
  key_task = asyncio.ensure_future(keys.__anext__())
  change_task = asyncio.ensure_future(app.changed.wait())
  tick = asyncio.ensure_future(asyncio.sleep(0.5))
  try:
    while True:
      done, _ = await asyncio.wait(
        {key_task, change_task, tick}, return_when=asyncio.FIRST_COMPLETED
      )
      redraw = False
      if change_task in done:
        app.changed.clear()
        change_task = asyncio.ensure_future(app.changed.wait())
        redraw = True
      if tick in done:
        tick = asyncio.ensure_future(asyncio.sleep(0.5))
        if terminal.size() != size:  # the window was resized
          size, redraw = terminal.size(), True
      if key_task in done:
        key = key_task.result()
        key_task = asyncio.ensure_future(keys.__anext__())
        if not await app.handle(key):
          return
        redraw = True
      if redraw:
        paint()
  finally:
    for task in (follower, key_task, change_task, tick):
      task.cancel()
    await asyncio.gather(follower, key_task, change_task, tick, return_exceptions=True)
