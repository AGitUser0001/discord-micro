"""Builders for message content: embeds, every component, modals, mentions.

Message components
    Button, StringSelect (alias Select), UserSelect, RoleSelect, MentionableSelect,
    ChannelSelect, ActionRow
    TextDisplay, Section, Thumbnail, MediaGallery (MediaItem), File, Separator,
    Container: the "components v2" layout set. Using any of them at the top level of
    a message sets the IS_COMPONENTS_V2 flag; such a message carries no `content` or
    `embeds`.
Modal components
    Modal(custom_id, title, [...]) holds Label (wrapping TextInput, a select,
    FileUpload, RadioGroup, CheckboxGroup or Checkbox) and TextDisplay.

Every builder has `to_dict()`, and `validate()` checks a payload against Discord's
own request models, constraints included. Anything a builder lacks can be passed as
a plain dict.
"""

import re
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, ClassVar, Literal

from pydantic import JsonValue

type Json = dict[str, JsonValue]

EPHEMERAL = 1 << 6
SUPPRESS_EMBEDS = 1 << 2
SUPPRESS_NOTIFICATIONS = 1 << 12
IS_COMPONENTS_V2 = 1 << 15

_BUTTON_STYLES = {
  "primary": 1,
  "secondary": 2,
  "success": 3,
  "danger": 4,
  "link": 5,
  "premium": 6,
}
_CHANNEL_TYPES = {
  "text": 0,
  "dm": 1,
  "voice": 2,
  "group_dm": 3,
  "category": 4,
  "announcement": 5,
  "announcement_thread": 10,
  "public_thread": 11,
  "private_thread": 12,
  "stage": 13,
  "directory": 14,
  "forum": 15,
}


# Interception ----------------------------------------------------------------------
#
# Middleware around building and serializing components, so a rule (sign every custom
# id, prefix them, forbid a style, add a tracking field) lives in one place instead of
# at every call site. Synchronous, because builders are.

type Only = type | tuple[type, ...] | None


@dataclass(slots=True)
class Construction:
  """A component about to be built: change `args` / `kwargs` before calling `next()`."""

  cls: type
  args: tuple[Any, ...]
  kwargs: dict[str, Any]


type BuildMiddleware = Callable[[Construction, Callable[[], Any]], Any]
"""`fn(call, next)`: return `next()` (the component), or a different one."""
type SerializeMiddleware = Callable[[Any, Callable[[], Json]], Json]
"""`fn(component, next)`: return `next()` (its JSON), changed or replaced."""


class Hooks:
  """The middleware that wraps component construction and serialization.

  Builders are frozen dataclasses; `Button(...)` runs the *build* middleware and
  `component.to_dict()` the *serialize* middleware (also when a message or modal
  serializes its children). Middleware nests in registration order: the first added is
  outermost. `only=` limits one to a component class (or a tuple of them, subclasses
  included). Raw dict components are plain JSON and bypass both.

      @hooks.serialize
      def sign_ids(component, next):
        data = next()
        if "custom_id" in data:
          data["custom_id"] = sign(data["custom_id"])
        return data
  """

  def __init__(self) -> None:
    self._build: list[tuple[BuildMiddleware, Only]] = []
    self._serialize: list[tuple[SerializeMiddleware, Only]] = []

  def build(self, function: BuildMiddleware | None = None, *, only: Only = None) -> Any:
    """Register construction middleware (a decorator, with or without `only=`)."""
    return self._add(self._build, function, only)

  def serialize(
    self, function: SerializeMiddleware | None = None, *, only: Only = None
  ) -> Any:
    """Register serialization middleware (a decorator, with or without `only=`)."""
    return self._add(self._serialize, function, only)

  def remove(self, function: Callable[..., Any]) -> bool:
    """Unregister a middleware of either kind; True if it was registered."""
    found = False
    for registry in (self._build, self._serialize):
      kept = [entry for entry in registry if entry[0] is not function]
      found = found or len(kept) != len(registry)
      registry[:] = kept
    return found

  @contextmanager
  def scoped(self) -> Iterator[Hooks]:
    """Restore the registered middleware on exit (for tests and one-off rules)."""
    saved = list(self._build), list(self._serialize)
    try:
      yield self
    finally:
      self._build[:], self._serialize[:] = saved

  def _add(self, registry: list[Any], function: Any, only: Only) -> Any:
    def register(function: Any) -> Any:
      registry.append((function, only))
      return function

    return register if function is None else register(function)

  def run_build(self, cls: type, args: tuple[Any, ...], kwargs: dict[str, Any]) -> Any:
    """Build `cls` through the build middleware. Components that middleware builds
    itself skip the build chain, so a middleware cannot recurse into itself."""
    chain = [fn for fn, only in self._build if _applies(only, cls)]
    call = Construction(cls, args, kwargs)

    def at(index: int) -> Any:
      if index == len(chain):
        return type.__call__(cls, *call.args, **call.kwargs)
      return chain[index](call, lambda: at(index + 1))

    token = _building.set(True)
    try:
      return at(0)
    finally:
      _building.reset(token)

  def run_serialize(self, component: Any, original: Callable[[Any], Json]) -> Json:
    """Serialize `component` through the serialize middleware."""
    chain = [fn for fn, only in self._serialize if _applies(only, type(component))]

    def at(index: int) -> Json:
      if index == len(chain):
        return original(component)
      return chain[index](component, lambda: at(index + 1))

    return at(0)

  @property
  def active(self) -> bool:
    """Whether any middleware is registered."""
    return bool(self._build or self._serialize)


def _applies(only: Only, cls: type) -> bool:
  return only is None or issubclass(cls, only)


_building: ContextVar[bool] = ContextVar("micro_ui_building", default=False)

hooks = Hooks()
"""The process-wide hooks every builder in this module runs."""


class _Hooked(type):
  """Metaclass of the builders: runs the build and serialize middleware."""

  def __new__(
    mcs, name: str, bases: tuple[type, ...], namespace: dict[str, Any]
  ) -> Any:
    original = namespace.get("to_dict")
    if original is not None and not getattr(original, "_hooked", False):

      def to_dict(self: Any, _original: Callable[[Any], Json] = original) -> Json:
        if not hooks._serialize:  # pyright: ignore[reportPrivateUsage]
          return _original(self)
        return hooks.run_serialize(self, _original)

      to_dict._hooked = True  # type: ignore[attr-defined]
      to_dict.__doc__ = original.__doc__
      namespace["to_dict"] = to_dict
    return super().__new__(mcs, name, bases, namespace)

  @property
  def max(cls) -> int | None:
    """What this kind of component can hold in its main dimension (read it on the class)."""
    return _primary_max(cls)

  def __call__(cls, *args: Any, **kwargs: Any) -> Any:
    if not hooks._build or _building.get():  # pyright: ignore[reportPrivateUsage]
      built = super().__call__(*args, **kwargs)
    else:
      built = hooks.run_build(cls, args, kwargs)
    if isinstance(built, _Measured):
      built._accumulate()  # pyright: ignore[reportPrivateUsage]
    return built


# Counts and limits -------------------------------------------------------------------
#
# Every component knows how much it holds: its own fields (a label's length, how many
# children a row has) and, accumulated up from its children as it is built, how many
# components and how many characters of text are inside it in all. Each count has the
# limit Discord gives it. Nothing is recomputed by walking JSON, and checking the limits
# is serialization middleware (`check_limits`), not part of building.

MAX_COMPONENTS = 40
"""Components in one message, counting every nested one."""
MAX_TEXT = 4000
"""Characters of Text Display content in one message, in all."""


@dataclass(frozen=True, slots=True)
class Measure:
  """One count with its limit: `Measure("content", 5200, limit=4000)` is over."""

  name: str
  count: int
  limit: int | None = None
  minimum: int = 0

  @property
  def ok(self) -> bool:
    """Whether the count is within `minimum` and `limit`."""
    return self.minimum <= self.count and (
      self.limit is None or self.count <= self.limit
    )

  def __str__(self) -> str:
    if self.count < self.minimum:
      return f"{self.name} is {self.count}; Discord needs at least {self.minimum}"
    return f"{self.name} is {self.count}; Discord allows {self.limit}"


def enforce(measures: Iterable[Measure], subject: str) -> None:
  """Raise ValueError naming every measure that is out of bounds."""
  broken = [str(m) for m in measures if not m.ok]
  if broken:
    raise ValueError(f"{subject}: {'; '.join(broken)}.")


def _tally(item: Any) -> tuple[int, int]:
  """`(components, text characters)` of anything that can sit in a message."""
  if isinstance(item, _Measured):
    return item.components_count, item.text_count
  if isinstance(item, str):  # a Section's plain-text shorthand is a Text Display
    return 1, len(item)
  if isinstance(item, Mapping):
    components, text = (
      1,
      len(item.get("content") or "") if item.get("type") == 10 else 0,
    )
    for child in item.get("components") or ():
      more, characters = _tally(child)
      components, text = components + more, text + characters
    if item.get("accessory"):
      more, characters = _tally(item["accessory"])
      components, text = components + more, text + characters
    return components, text
  return 1, 0


def message_measures(components: Sequence[Any] | Any) -> tuple[Measure, ...]:
  """A message's totals against Discord's two message-wide limits."""
  items = components if isinstance(components, list | tuple) else [components]
  components_in_all = text_in_all = 0
  for item in items:
    more, characters = _tally(item)
    components_in_all, text_in_all = components_in_all + more, text_in_all + characters
  return (
    Measure("components in all", components_in_all, MAX_COMPONENTS),
    Measure("text in all", text_in_all, MAX_TEXT),
  )


class _Measured(metaclass=_Hooked):
  """Base of every component: its counts, accumulated as it is constructed."""

  __slots__ = ("components_count", "text_count")
  components_count: int
  """This component and everything inside it."""
  text_count: int
  """Characters of Text Display content inside it, in all."""
  slots: ClassVar[int] = 1
  """What it costs inside its parent's `count`: 1, but a select takes a whole row (5)."""

  @property
  def count(self) -> int:
    """How much of its main dimension it holds (see `max`): an action row's slots used,
    a section's texts, a gallery's items, a text's characters, a container's components."""
    return _PRIMARY[type(self)][0](self)

  @property
  def max(self) -> int | None:
    """The limit of `count` (None when it has no main dimension)."""
    return _primary_max(type(self))

  @property
  def remaining(self) -> int | None:
    """`max - count`: how much more fits (None when unbounded)."""
    return None if self.max is None else self.max - self.count

  def _children(self) -> Iterable[Any]:
    return ()

  def _text(self) -> int:
    return 0

  def _counts(self) -> Mapping[str, int]:
    """This component's own counts, by Discord's field name."""
    return {}

  def _accumulate(self) -> None:
    components, text = 1, self._text()
    for child in self._children():
      more, characters = _tally(child)
      components, text = components + more, text + characters
    object.__setattr__(self, "components_count", components)
    object.__setattr__(self, "text_count", text)

  @property
  def measures(self) -> tuple[Measure, ...]:
    """Every count this component has, with its limit (from Discord's own models)."""
    limits = _limits_of(type(self))
    found = [
      Measure(
        "slots" if isinstance(self, ActionRow) and name == "components" else name,
        count,
        limits.get(name, (0, None))[1],
        limits.get(name, (0, None))[0],
      )
      for name, count in self._counts().items()
    ]
    found.append(Measure("components in all", self.components_count, MAX_COMPONENTS))
    found.append(Measure("text in all", self.text_count, MAX_TEXT))
    return tuple(found)


def _slots(item: Any) -> int:
  """How many slots of an action row a child takes (a select takes all five)."""
  if isinstance(item, Mapping):
    return 5 if item.get("type") in (3, 5, 6, 7, 8) else 1
  return getattr(item, "slots", 1)


def _lengths(**fields: Any) -> dict[str, int]:
  """`len()` of each field that is set."""
  return {name: len(value) for name, value in fields.items() if value is not None}


def check_limits(component: Any, next: Callable[[], Json]) -> Json:
  """Serialization middleware (registered by default): refuse a component over a limit.

  Remove it with `hooks.remove(check_limits)` to send what Discord would reject.
  """
  if isinstance(component, _Measured):
    enforce(component.measures, type(component).__name__)
  return next()


def _put(data: Json, **items: JsonValue) -> Json:
  """Add the items that are not None."""
  for key, item in items.items():
    if item is not None:
      data[key] = item
  return data


# Mentions and embeds -----------------------------------------------------------


@dataclass(frozen=True, slots=True)
class AllowedMentions(metaclass=_Hooked):
  """Which mentions in a message may ping. Micro defaults to `none()`."""

  parse: tuple[Literal["users", "roles", "everyone"], ...] = ()
  users: tuple[int, ...] = ()
  roles: tuple[int, ...] = ()
  replied_user: bool = False

  @classmethod
  def none(cls) -> AllowedMentions:
    """Allow no mention to ping."""
    return cls()

  @classmethod
  def everything(cls) -> AllowedMentions:
    """Allow every mention to ping."""
    return cls(parse=("users", "roles", "everyone"), replied_user=True)

  @classmethod
  def only(
    cls, *, users: Iterable[int] = (), roles: Iterable[int] = ()
  ) -> AllowedMentions:
    """Allow only the given users and roles (and optionally replied-to users) to ping."""
    return cls(users=tuple(users), roles=tuple(roles))

  def to_dict(self) -> Json:
    """This as Discord's `allowed_mentions` object."""
    value: Json = {"parse": list(self.parse), "replied_user": self.replied_user}
    if self.users:
      value["users"] = [str(user) for user in self.users]
    if self.roles:
      value["roles"] = [str(role) for role in self.roles]
    return value


def embed(
  title: str | None = None,
  description: str | None = None,
  *,
  color: int | None = None,
  url: str | None = None,
  fields: Sequence[tuple[str, str] | tuple[str, str, bool]] = (),
  footer: str | None = None,
  footer_icon: str | None = None,
  image: str | None = None,
  thumbnail: str | None = None,
  author: str | None = None,
  author_url: str | None = None,
  author_icon: str | None = None,
  timestamp: datetime | str | None = None,
) -> Json:
  """Build an embed; `fields` are `(name, value)` or `(name, value, inline)`."""
  value: Json = {}
  _put(value, title=title, description=description, color=color, url=url)
  if timestamp is not None:
    value["timestamp"] = (
      timestamp.isoformat() if isinstance(timestamp, datetime) else timestamp
    )
  if fields:
    value["fields"] = [
      {
        "name": item[0],
        "value": item[1],
        "inline": bool(item[2]) if len(item) > 2 else False,
      }
      for item in fields
    ]
  if footer is not None:
    value["footer"] = _put({"text": footer}, icon_url=footer_icon)
  if image is not None:
    value["image"] = {"url": image}
  if thumbnail is not None:
    value["thumbnail"] = {"url": thumbnail}
  if author is not None:
    value["author"] = _put({"name": author}, url=author_url, icon_url=author_icon)
  return value


# Emoji -------------------------------------------------------------------------

_CUSTOM_EMOJI = re.compile(r"<(a?):(\w{2,32}):(\d+)>")


@dataclass(frozen=True, slots=True)
class Emoji(metaclass=_Hooked):
  """A unicode emoji (`Emoji("🙂")`) or a custom one (`Emoji("name", 123456)`)."""

  name: str
  id: int | str | None = None
  animated: bool = False

  @classmethod
  def parse(cls, text: str) -> Emoji:
    """`🙂`, `<:name:123>` or `<a:name:123>`."""
    if found := _CUSTOM_EMOJI.fullmatch(text):
      animated, name, identifier = found.groups()
      return cls(name, identifier, bool(animated))
    return cls(text)

  def to_dict(self) -> Json:
    """This component as the JSON object Discord expects."""
    return _put({"name": self.name}, id=None if self.id is None else str(self.id))


def _emoji(value: str | Emoji | None) -> Json | None:
  if value is None:
    return None
  return (value if isinstance(value, Emoji) else Emoji.parse(value)).to_dict()


# Buttons and selects -----------------------------------------------------------

type ButtonStyle = Literal[
  "primary", "secondary", "success", "danger", "link", "premium"
]


@dataclass(frozen=True, slots=True)
class Button(_Measured):
  """A button: `custom_id` (an interaction), `url` (a link), or `sku_id` (premium)."""

  label: str | None = None
  custom_id: str | None = None
  url: str | None = None
  style: ButtonStyle = "primary"
  emoji: str | Emoji | None = None
  disabled: bool = False
  sku_id: int | str | None = None
  id: int | None = None

  def __post_init__(self) -> None:
    targets = [x for x in (self.custom_id, self.url, self.sku_id) if x is not None]
    if len(targets) != 1:
      raise ValueError("A button needs exactly one of custom_id, url or sku_id.")
    if self.sku_id is not None and (self.label is not None or self.emoji is not None):
      raise ValueError("A premium button has no label or emoji.")

  def to_dict(self) -> Json:
    """This component as the JSON object Discord expects."""
    kind = "premium" if self.sku_id is not None else "link" if self.url else self.style
    value: Json = {"type": 2, "style": _BUTTON_STYLES[kind], "disabled": self.disabled}
    _put(value, id=self.id, label=self.label, custom_id=self.custom_id, url=self.url)
    if self.sku_id is not None:
      value["sku_id"] = str(self.sku_id)
    _put(value, emoji=_emoji(self.emoji))
    return value


@dataclass(frozen=True, slots=True)
class SelectOption(metaclass=_Hooked):
  """One option of a string select."""

  label: str
  value: str
  description: str | None = None
  default: bool = False
  emoji: str | Emoji | None = None

  def to_dict(self) -> Json:
    """This component as the JSON object Discord expects."""
    value: Json = {"label": self.label, "value": self.value, "default": self.default}
    return _put(value, description=self.description, emoji=_emoji(self.emoji))


@dataclass(frozen=True, slots=True)
class Default(metaclass=_Hooked):
  """A preselected entry of a user, role, mentionable or channel select."""

  type: Literal["user", "role", "channel"]
  id: int | str

  @classmethod
  def user(cls, id: int | str) -> Default:
    """A default selection of a user."""
    return cls("user", id)

  @classmethod
  def role(cls, id: int | str) -> Default:
    """A default selection of a role."""
    return cls("role", id)

  @classmethod
  def channel(cls, id: int | str) -> Default:
    """A default selection of a channel."""
    return cls("channel", id)

  def to_dict(self) -> Json:
    """This as a Discord default-value object."""
    return {"type": self.type, "id": str(self.id)}


def _defaults(
  kind: Literal["user", "role", "channel"] | None, values: Sequence[int | str | Default]
) -> list[Json]:
  found: list[Json] = []
  for item in values:
    if isinstance(item, Default):
      found.append(item.to_dict())
    elif kind is None:
      raise ValueError("A mentionable select's defaults are Default.user/role(id).")
    else:
      found.append(Default(kind, item).to_dict())
  return found


def _select(
  type_: int,
  custom_id: str,
  placeholder: str | None,
  min_values: int | None,
  max_values: int | None,
  disabled: bool,
  required: bool | None,
  id: int | None,
  **more: Any,
) -> Json:
  value: Json = {"type": type_, "custom_id": custom_id, "disabled": disabled}
  _put(
    value,
    id=id,
    placeholder=placeholder,
    min_values=min_values,
    max_values=max_values,
    required=required,
  )
  return _put(value, **more)


@dataclass(frozen=True, slots=True)
class StringSelect(_Measured):
  """A menu of string options; options may be plain strings or `SelectOption`s."""

  custom_id: str
  options: Sequence[SelectOption | str]
  placeholder: str | None = None
  min_values: int | None = None
  max_values: int | None = None
  disabled: bool = False
  required: bool | None = None
  id: int | None = None

  def to_dict(self) -> Json:
    """This component as the JSON object Discord expects."""
    options = [
      o if isinstance(o, SelectOption) else SelectOption(o, o) for o in self.options
    ]
    return _select(
      3, self.custom_id, self.placeholder, self.min_values, self.max_values,
      self.disabled, self.required, self.id,
      options=[o.to_dict() for o in options],
    )  # fmt: skip


Select = StringSelect
"""The older name for `StringSelect`."""


@dataclass(frozen=True, slots=True)
class UserSelect(_Measured):
  """A menu of users."""

  custom_id: str
  placeholder: str | None = None
  min_values: int | None = None
  max_values: int | None = None
  disabled: bool = False
  required: bool | None = None
  defaults: Sequence[int | str | Default] = ()
  id: int | None = None

  def to_dict(self) -> Json:
    """This component as the JSON object Discord expects."""
    return _select(
      5, self.custom_id, self.placeholder, self.min_values, self.max_values,
      self.disabled, self.required, self.id,
      default_values=_defaults("user", self.defaults) or None,
    )  # fmt: skip


@dataclass(frozen=True, slots=True)
class RoleSelect(_Measured):
  """A menu of server roles."""

  custom_id: str
  placeholder: str | None = None
  min_values: int | None = None
  max_values: int | None = None
  disabled: bool = False
  required: bool | None = None
  defaults: Sequence[int | str | Default] = ()
  id: int | None = None

  def to_dict(self) -> Json:
    """This component as the JSON object Discord expects."""
    return _select(
      6, self.custom_id, self.placeholder, self.min_values, self.max_values,
      self.disabled, self.required, self.id,
      default_values=_defaults("role", self.defaults) or None,
    )  # fmt: skip


@dataclass(frozen=True, slots=True)
class MentionableSelect(_Measured):
  """Users and roles together; `defaults` are `Default.user(id)` / `Default.role(id)`."""

  custom_id: str
  placeholder: str | None = None
  min_values: int | None = None
  max_values: int | None = None
  disabled: bool = False
  required: bool | None = None
  defaults: Sequence[Default] = ()
  id: int | None = None

  def to_dict(self) -> Json:
    """This component as the JSON object Discord expects."""
    return _select(
      7, self.custom_id, self.placeholder, self.min_values, self.max_values,
      self.disabled, self.required, self.id,
      default_values=_defaults(None, self.defaults) or None,
    )  # fmt: skip


@dataclass(frozen=True, slots=True)
class ChannelSelect(_Measured):
  """Channels; `channel_types` limits them: `"text"`, `"voice"`, `"category"`, ..."""

  custom_id: str
  placeholder: str | None = None
  min_values: int | None = None
  max_values: int | None = None
  disabled: bool = False
  required: bool | None = None
  channel_types: Sequence[str | int] = ()
  defaults: Sequence[int | str | Default] = ()
  id: int | None = None

  def to_dict(self) -> Json:
    """This component as the JSON object Discord expects."""
    kinds = [_CHANNEL_TYPES[t] if isinstance(t, str) else t for t in self.channel_types]
    return _select(
      8, self.custom_id, self.placeholder, self.min_values, self.max_values,
      self.disabled, self.required, self.id,
      channel_types=kinds or None,
      default_values=_defaults("channel", self.defaults) or None,
    )  # fmt: skip


type Select_ = (
  StringSelect | UserSelect | RoleSelect | MentionableSelect | ChannelSelect
)
_SELECTS = (StringSelect, UserSelect, RoleSelect, MentionableSelect, ChannelSelect)
type Component = Button | Select_


@dataclass(frozen=True, slots=True)
class ActionRow(_Measured):
  """Up to five buttons, or one select."""

  components: Sequence[Component]
  id: int | None = None

  def __init__(self, *components: Component, id: int | None = None) -> None:
    object.__setattr__(self, "components", tuple(components))
    object.__setattr__(self, "id", id)

  def to_dict(self) -> Json:
    """This component as the JSON object Discord expects."""
    return _put(
      {"type": 1, "components": [c.to_dict() for c in self.components]}, id=self.id
    )


# Layout components (v2) ---------------------------------------------------------


@dataclass(frozen=True, slots=True)
class TextDisplay(_Measured):
  """Markdown text. Counts toward the message's 4000 characters of text in total."""

  content: str
  id: int | None = None

  def to_dict(self) -> Json:
    """This component as the JSON object Discord expects."""
    return _put({"type": 10, "content": self.content}, id=self.id)


@dataclass(frozen=True, slots=True)
class Thumbnail(_Measured):
  """A small image beside text: only as a `Section` accessory."""

  url: str
  description: str | None = None
  spoiler: bool = False
  id: int | None = None

  def to_dict(self) -> Json:
    """This component as the JSON object Discord expects."""
    value: Json = {"type": 11, "media": {"url": self.url}, "spoiler": self.spoiler}
    return _put(value, id=self.id, description=self.description)


@dataclass(frozen=True, slots=True)
class Section(_Measured):
  """One to three texts with a `Button` or `Thumbnail` beside them."""

  texts: Sequence[TextDisplay | str]
  accessory: Button | Thumbnail
  id: int | None = None

  def __init__(
    self,
    *texts: TextDisplay | str,
    accessory: Button | Thumbnail,
    id: int | None = None,
  ) -> None:
    object.__setattr__(self, "texts", tuple(texts))
    object.__setattr__(self, "accessory", accessory)
    object.__setattr__(self, "id", id)

  def to_dict(self) -> Json:
    """This component as the JSON object Discord expects."""
    texts = [t if isinstance(t, TextDisplay) else TextDisplay(t) for t in self.texts]
    value: Json = {
      "type": 9,
      "components": [t.to_dict() for t in texts],
      "accessory": self.accessory.to_dict(),
    }
    return _put(value, id=self.id)


@dataclass(frozen=True, slots=True)
class MediaItem(metaclass=_Hooked):
  """One picture or video of a `MediaGallery`: a URL or `attachment://name`."""

  url: str
  description: str | None = None
  spoiler: bool = False

  def to_dict(self) -> Json:
    """This component as the JSON object Discord expects."""
    value: Json = {"media": {"url": self.url}, "spoiler": self.spoiler}
    return _put(value, description=self.description)


@dataclass(frozen=True, slots=True)
class MediaGallery(_Measured):
  """Up to ten pictures or videos."""

  items: Sequence[MediaItem | str]
  id: int | None = None

  def __init__(self, *items: MediaItem | str, id: int | None = None) -> None:
    object.__setattr__(self, "items", tuple(items))
    object.__setattr__(self, "id", id)

  def to_dict(self) -> Json:
    """This component as the JSON object Discord expects."""
    items = [i if isinstance(i, MediaItem) else MediaItem(i) for i in self.items]
    return _put({"type": 12, "items": [i.to_dict() for i in items]}, id=self.id)


@dataclass(frozen=True, slots=True)
class File(_Measured):
  """An uploaded file shown in the message; `url` is `attachment://name`."""

  url: str
  spoiler: bool = False
  id: int | None = None

  def __post_init__(self) -> None:
    if not self.url.startswith("attachment://"):
      raise ValueError("A File component shows an attachment: use attachment://name.")

  def to_dict(self) -> Json:
    """This component as the JSON object Discord expects."""
    value: Json = {"type": 13, "file": {"url": self.url}, "spoiler": self.spoiler}
    return _put(value, id=self.id)


@dataclass(frozen=True, slots=True)
class Separator(_Measured):
  """Space between components, with an optional dividing line."""

  divider: bool = True
  spacing: Literal["small", "large"] = "small"
  id: int | None = None

  def to_dict(self) -> Json:
    """This component as the JSON object Discord expects."""
    value: Json = {
      "type": 14,
      "divider": self.divider,
      "spacing": 1 if self.spacing == "small" else 2,
    }
    return _put(value, id=self.id)


@dataclass(frozen=True, slots=True)
class Container(_Measured):
  """A bordered box of components with an optional accent colour."""

  components: Sequence[Any]
  accent_color: int | None = None
  spoiler: bool = False
  id: int | None = None

  def __init__(
    self,
    *components: Any,
    accent_color: int | None = None,
    spoiler: bool = False,
    id: int | None = None,
  ) -> None:
    object.__setattr__(self, "components", tuple(components))
    object.__setattr__(self, "accent_color", accent_color)
    object.__setattr__(self, "spoiler", spoiler)
    object.__setattr__(self, "id", id)

  def to_dict(self) -> Json:
    """This component as the JSON object Discord expects."""
    value: Json = {
      "type": 17,
      "components": rows(self.components),
      "spoiler": self.spoiler,
    }
    return _put(value, id=self.id, accent_color=self.accent_color)


_LAYOUT = (TextDisplay, Section, Thumbnail, MediaGallery, File, Separator, Container)
type Buildable = (
  Component
  | ActionRow
  | TextDisplay
  | Section
  | MediaGallery
  | File
  | Separator
  | Container
)
"""Anything that can be a top-level component of a message."""


def rows(components: Sequence[Any]) -> list[JsonValue]:
  """Lay out components: loose buttons fill rows of five, loose selects get a row.

  Rows and layout components stay as they are; a plain dict passes through.
  """
  laid_out: list[JsonValue] = []
  buttons: list[Button] = []

  def flush() -> None:
    while buttons:
      laid_out.append(ActionRow(*buttons[:5]).to_dict())
      del buttons[:5]

  for item in components:
    if isinstance(item, Button):
      buttons.append(item)
      continue
    flush()
    if isinstance(item, Mapping):
      laid_out.append(dict(item))
    elif isinstance(item, _SELECTS):
      laid_out.append(ActionRow(item).to_dict())
    else:
      laid_out.append(item.to_dict())
  flush()
  return laid_out


def is_v2(components: Sequence[Any] | None) -> bool:
  """Whether a message's components use the layout set (so it is a v2 message)."""
  return any(
    isinstance(item, _LAYOUT)
    or (isinstance(item, Mapping) and item.get("type") in (9, 10, 11, 12, 13, 14, 17))
    for item in components or ()
  )


# Modal components ---------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class TextInput(_Measured):
  """A text field. In a `Label`, leave `label` out; bare in a `Modal`, it needs one."""

  custom_id: str
  label: str | None = None
  style: Literal["short", "paragraph"] = "short"
  required: bool = True
  placeholder: str | None = None
  value: str | None = None
  min_length: int | None = None
  max_length: int | None = None
  id: int | None = None

  def to_dict(self) -> Json:
    """This component as the JSON object Discord expects."""
    data: Json = {
      "type": 4,
      "custom_id": self.custom_id,
      "style": 1 if self.style == "short" else 2,
      "required": self.required,
    }
    return _put(
      data,
      id=self.id,
      label=self.label,
      placeholder=self.placeholder,
      value=self.value,
      min_length=self.min_length,
      max_length=self.max_length,
    )


@dataclass(frozen=True, slots=True)
class GroupOption(metaclass=_Hooked):
  """An option of a `RadioGroup` or `CheckboxGroup`."""

  label: str
  value: str
  description: str | None = None
  default: bool = False

  def to_dict(self) -> Json:
    """This component as the JSON object Discord expects."""
    value: Json = {"label": self.label, "value": self.value, "default": self.default}
    return _put(value, description=self.description)


def _group(options: Sequence[GroupOption | str]) -> list[JsonValue]:
  return [
    (o if isinstance(o, GroupOption) else GroupOption(o, o)).to_dict() for o in options
  ]


@dataclass(frozen=True, slots=True)
class RadioGroup(_Measured):
  """Pick exactly one of two to ten options."""

  custom_id: str
  options: Sequence[GroupOption | str]
  required: bool | None = None
  id: int | None = None

  def to_dict(self) -> Json:
    """This component as the JSON object Discord expects."""
    value: Json = {
      "type": 21,
      "custom_id": self.custom_id,
      "options": _group(self.options),
    }
    return _put(value, id=self.id, required=self.required)


@dataclass(frozen=True, slots=True)
class CheckboxGroup(_Measured):
  """Pick any of up to ten options (`min_values`, `max_values` limit how many)."""

  custom_id: str
  options: Sequence[GroupOption | str]
  min_values: int | None = None
  max_values: int | None = None
  required: bool | None = None
  id: int | None = None

  def to_dict(self) -> Json:
    """This component as the JSON object Discord expects."""
    value: Json = {
      "type": 22,
      "custom_id": self.custom_id,
      "options": _group(self.options),
    }
    return _put(
      value,
      id=self.id,
      min_values=self.min_values,
      max_values=self.max_values,
      required=self.required,
    )


@dataclass(frozen=True, slots=True)
class Checkbox(_Measured):
  """A single yes/no box."""

  custom_id: str
  default: bool | None = None
  id: int | None = None

  def to_dict(self) -> Json:
    """This component as the JSON object Discord expects."""
    return _put(
      {"type": 23, "custom_id": self.custom_id}, id=self.id, default=self.default
    )


@dataclass(frozen=True, slots=True)
class FileUpload(_Measured):
  """Ask for files; read them with `ctx.attachments` after the submission."""

  custom_id: str
  min_values: int | None = None
  max_values: int | None = None
  required: bool | None = None
  file_types: Sequence[str] = ()
  id: int | None = None

  def to_dict(self) -> Json:
    """This component as the JSON object Discord expects."""
    value: Json = {"type": 19, "custom_id": self.custom_id}
    return _put(
      value,
      id=self.id,
      min_values=self.min_values,
      max_values=self.max_values,
      required=self.required,
      file_types=list(self.file_types) or None,
    )


type ModalInput = (
  TextInput | Select_ | RadioGroup | CheckboxGroup | Checkbox | FileUpload
)


@dataclass(frozen=True, slots=True)
class Label(_Measured):
  """A titled field of a modal: wraps one input and gives it a label and a hint."""

  label: str
  component: ModalInput
  description: str | None = None
  id: int | None = None

  def to_dict(self) -> Json:
    """This component as the JSON object Discord expects."""
    value: Json = {
      "type": 18,
      "label": self.label,
      "component": self.component.to_dict(),
    }
    return _put(value, id=self.id, description=self.description)


@dataclass(frozen=True, slots=True)
class Modal(_Measured):
  """A pop-up form of up to five `Label`s and `TextDisplay`s.

  A bare `TextInput` (with a label) is still accepted and sent in the older way.
  """

  custom_id: str
  title: str
  components: Sequence[Label | TextDisplay | TextInput | Mapping[str, Any]] = field(
    default_factory=tuple
  )

  @property
  def inputs(self) -> Sequence[Label | TextDisplay | TextInput | Mapping[str, Any]]:
    """The modal's components, as a sequence."""
    return self.components

  def to_dict(self) -> Json:
    """This component as the JSON object Discord expects."""
    built: list[JsonValue] = []
    for item in self.components:
      if isinstance(item, TextInput):
        if item.label is None:
          raise ValueError("A bare TextInput needs a label; or wrap it in Label(...).")
        built.append({"type": 1, "components": [item.to_dict()]})
      elif isinstance(item, Mapping):
        built.append(dict(item))
      else:
        built.append(item.to_dict())
    return {"custom_id": self.custom_id, "title": self.title, "components": built}


# Messages -----------------------------------------------------------------------


def message_body(
  content: str | None = None,
  *,
  embeds: Sequence[Json] = (),
  components: Sequence[Any] | None = None,
  allowed_mentions: AllowedMentions | None = None,
  ephemeral: bool = False,
  flags: int = 0,
) -> Json:
  """A message payload with safe mention defaults.

  Layout components set IS_COMPONENTS_V2, and such a message has no `content` or
  `embeds` (Discord rejects both).
  """
  body: Json = {
    "allowed_mentions": (allowed_mentions or AllowedMentions.none()).to_dict()
  }
  if is_v2(components):
    if content is not None or embeds:
      raise ValueError(
        "A message with layout components (TextDisplay, Container, ...) has no "
        "content or embeds: put the text in a TextDisplay."
      )
    flags |= IS_COMPONENTS_V2
  if content is not None:
    body["content"] = content
  if embeds:
    body["embeds"] = list(embeds)
  if components is not None:
    body["components"] = laid_out = rows(components)
    enforce(message_measures(laid_out), "This message")
  if ephemeral:
    flags |= EPHEMERAL
  if flags:
    body["flags"] = flags
  return body


# Validation ---------------------------------------------------------------------

_MESSAGE_MODELS = {
  1: "ActionRowComponentForMessageRequest",
  2: "ButtonComponentForMessageRequest",
  3: "StringSelectComponentForMessageRequest",
  5: "UserSelectComponentForMessageRequest",
  6: "RoleSelectComponentForMessageRequest",
  7: "MentionableSelectComponentForMessageRequest",
  8: "ChannelSelectComponentForMessageRequest",
  9: "SectionComponentForMessageRequest",
  10: "TextDisplayComponentForMessageRequest",
  11: "ThumbnailComponentForMessageRequest",
  12: "MediaGalleryComponentForMessageRequest",
  13: "FileComponentForMessageRequest",
  14: "SeparatorComponentForMessageRequest",
  17: "ContainerComponentForMessageRequest",
}
_MODAL_MODELS = {
  1: "ActionRowComponentForModalRequest",
  3: "StringSelectComponentForModalRequest",
  4: "TextInputComponentForModalRequest",
  5: "UserSelectComponentForModalRequest",
  6: "RoleSelectComponentForModalRequest",
  7: "MentionableSelectComponentForModalRequest",
  8: "ChannelSelectComponentForModalRequest",
  10: "TextDisplayComponentForModalRequest",
  18: "LabelComponentForModalRequest",
  19: "FileUploadComponentForModalRequest",
  21: "RadioGroupComponentForModalRequest",
  22: "CheckboxGroupComponentForModalRequest",
  23: "CheckboxComponentForModalRequest",
}


def validate(components: Sequence[Any] | Any, *, modal: bool = False) -> None:
  """Check components against Discord's request models; ValueError if one is wrong.

  Accepts a builder, a dict, or a list of either; `modal=True` checks modal rules.
  """
  from pydantic import ValidationError

  from micro.discord.models import http as models

  table = _MODAL_MODELS if modal else _MESSAGE_MODELS
  items: Sequence[Any] = (
    components if isinstance(components, list | tuple) else [components]
  )
  if not modal:
    enforce(message_measures(items), "This message")
  for item in items:
    payload: Mapping[str, Any] = item if isinstance(item, Mapping) else item.to_dict()
    name = table.get(payload.get("type", -1))
    if name is None:
      raise ValueError(f"Component type {payload.get('type')!r} is not valid here.")
    try:
      getattr(models, name).model_validate(payload)
    except ValidationError as error:
      problems = "; ".join(
        f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in error.errors()[:3]
      )
      raise ValueError(f"{name}: {problems}") from error


# What each component counts ------------------------------------------------------------
#
# For every component: the components inside it (`children`), the Text Display characters
# it holds itself (`text`), and its own counts by Discord's field name (`counts`). The
# limits are not repeated here: they are read from Discord's generated request models,
# so they cannot drift from what Discord enforces.

_COUNTED: dict[type, dict[str, Callable[[Any], Any]]] = {
  ActionRow: {
    "children": lambda c: c.components,
    "counts": lambda c: {"components": sum(_slots(i) for i in c.components)},
  },
  Button: {"counts": lambda c: _lengths(label=c.label, custom_id=c.custom_id)},
  StringSelect: {
    "counts": lambda c: _lengths(
      custom_id=c.custom_id, options=c.options, placeholder=c.placeholder
    )
  },
  UserSelect: {
    "counts": lambda c: _lengths(
      custom_id=c.custom_id, placeholder=c.placeholder, default_values=c.defaults
    )
  },
  RoleSelect: {
    "counts": lambda c: _lengths(
      custom_id=c.custom_id, placeholder=c.placeholder, default_values=c.defaults
    )
  },
  MentionableSelect: {
    "counts": lambda c: _lengths(
      custom_id=c.custom_id, placeholder=c.placeholder, default_values=c.defaults
    )
  },
  ChannelSelect: {
    "counts": lambda c: _lengths(
      custom_id=c.custom_id, placeholder=c.placeholder, default_values=c.defaults
    )
  },
  TextDisplay: {
    "text": lambda c: len(c.content),
    "counts": lambda c: {"content": len(c.content)},
  },
  Thumbnail: {"counts": lambda c: _lengths(description=c.description)},
  Section: {
    "children": lambda c: (*c.texts, c.accessory),
    "counts": lambda c: {"components": len(c.texts)},
  },
  MediaGallery: {"counts": lambda c: {"items": len(c.items)}},
  Container: {
    "children": lambda c: c.components,
    "counts": lambda c: {"components": len(c.components)},
  },
  TextInput: {
    "counts": lambda c: _lengths(
      custom_id=c.custom_id, label=c.label, value=c.value, placeholder=c.placeholder
    )
  },
  Label: {
    "children": lambda c: (c.component,),
    "counts": lambda c: _lengths(label=c.label, description=c.description),
  },
  FileUpload: {"counts": lambda c: _lengths(custom_id=c.custom_id)},
  RadioGroup: {"counts": lambda c: _lengths(custom_id=c.custom_id, options=c.options)},
  CheckboxGroup: {
    "counts": lambda c: _lengths(custom_id=c.custom_id, options=c.options)
  },
  Checkbox: {"counts": lambda c: _lengths(custom_id=c.custom_id)},
  Modal: {
    "children": lambda c: c.components,
    "counts": lambda c: {
      "title": len(c.title),
      "custom_id": len(c.custom_id),
      "components": len(c.components),
    },
  },
}
for _cls, _how in _COUNTED.items():
  for _name, _function in _how.items():
    setattr(_cls, f"_{_name}", lambda self, _f=_function: _f(self))

# The main dimension of each component: (what it holds, which limit bounds it). The limit
# is a field of Discord's model, or a number. This is `count` and `max`.
_PRIMARY: dict[type, tuple[Callable[[Any], int], str | int | None]] = {
  ActionRow: (lambda c: sum(_slots(i) for i in c.components), "components"),
  Button: (lambda c: len(c.label or ""), "label"),
  StringSelect: (lambda c: len(c.options), "options"),
  UserSelect: (lambda c: len(c.defaults or ()), "default_values"),
  RoleSelect: (lambda c: len(c.defaults or ()), "default_values"),
  MentionableSelect: (lambda c: len(c.defaults or ()), "default_values"),
  ChannelSelect: (lambda c: len(c.defaults or ()), "default_values"),
  TextDisplay: (lambda c: len(c.content), "content"),
  Thumbnail: (lambda c: len(c.description or ""), "description"),
  Section: (lambda c: len(c.texts), "components"),
  MediaGallery: (lambda c: len(c.items), "items"),
  File: (lambda c: 0, None),
  Separator: (lambda c: 0, None),
  Container: (lambda c: c.components_count, MAX_COMPONENTS),
  TextInput: (lambda c: len(c.value or ""), "value"),
  Label: (lambda c: len(c.label), "label"),
  FileUpload: (lambda c: 0, None),
  RadioGroup: (lambda c: len(c.options), "options"),
  CheckboxGroup: (lambda c: len(c.options), "options"),
  Checkbox: (lambda c: 0, None),
  Modal: (lambda c: len(c.components), "components"),
}
for _wide in (StringSelect, UserSelect, RoleSelect, MentionableSelect, ChannelSelect):
  _wide.slots = 5


def _primary_max(cls: type) -> int | None:
  entry = _PRIMARY.get(cls)
  if entry is None or entry[1] is None:
    return None
  if isinstance(entry[1], int):
    return entry[1]
  return _limits_of(cls).get(entry[1], (0, None))[1]


_TYPE_CODES: dict[type, int] = {
  ActionRow: 1, Button: 2, StringSelect: 3, TextInput: 4, UserSelect: 5,
  RoleSelect: 6, MentionableSelect: 7, ChannelSelect: 8, Section: 9, TextDisplay: 10,
  Thumbnail: 11, MediaGallery: 12, File: 13, Separator: 14, Container: 17, Label: 18,
  FileUpload: 19, RadioGroup: 21, CheckboxGroup: 22, Checkbox: 23,
}  # fmt: skip
_NOT_IN_A_MODEL: dict[type, dict[str, tuple[int, int | None]]] = {
  Modal: {"title": (1, 45), "custom_id": (1, 100), "components": (1, 5)}
}
_limit_cache: dict[type, dict[str, tuple[int, int | None]]] = {}


def _limits_of(cls: type) -> dict[str, tuple[int, int | None]]:
  """`{field: (minimum, maximum)}` for a component, from Discord's generated models."""
  if cls in _NOT_IN_A_MODEL:
    return _NOT_IN_A_MODEL[cls]
  if cls not in _limit_cache:
    import typing

    import annotated_types

    from micro.discord.models import http as models

    code = _TYPE_CODES[cls]
    model = getattr(models, _MESSAGE_MODELS.get(code) or _MODAL_MODELS[code])
    found: dict[str, tuple[int, int | None]] = {}
    for name, info in model.model_fields.items():
      low: Any = 0
      high: Any = None
      layers = [info.metadata] + [
        getattr(arg, "__metadata__", ()) for arg in typing.get_args(info.annotation)
      ]
      for layer in layers:
        for rule in layer:
          if isinstance(rule, annotated_types.MinLen):
            low = rule.min_length
          elif isinstance(rule, annotated_types.MaxLen):
            high = rule.max_length
          elif isinstance(rule, annotated_types.Interval):
            low = rule.ge if rule.ge is not None else low
            high = rule.le if rule.le is not None else high
          else:
            low = getattr(rule, "min_length", None) or low
            high = getattr(rule, "max_length", None) or high
      found[name] = (int(low), None if high is None else int(high))
    _limit_cache[cls] = found
  return _limit_cache[cls]


hooks.serialize(check_limits)  # the limits are checked as components are serialized
