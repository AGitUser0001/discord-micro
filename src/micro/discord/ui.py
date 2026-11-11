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
from os import PathLike
from typing import TYPE_CHECKING, Any, ClassVar, Literal, cast, overload

from pydantic import JsonValue

from .colour import Colour, ColourLike

if TYPE_CHECKING:
  from .objects import Object

from .enums import ButtonStyle, ChannelType, TextInputStyle

type Json = dict[str, JsonValue]


@dataclass(frozen=True, slots=True)
class Upload:
  """A file to send with a message.

      chart = Upload("chart.png", png_bytes)
      await interaction.respond(Draft(components=[MediaGallery(MediaItem(chart))]))   # shown, attached
      await interaction.respond(Draft("the log", files=[Upload.text("log.txt", text)]))

  Put it wherever a picture or file goes (`Thumbnail`, `MediaGallery`, `File`, an
  embed's `image=`) and the message attaches it by itself; a file that is only
  attached, not shown, goes in `files=`. `description` is its alt text.
  `spoiler` hides it behind a click.
  """

  filename: str
  data: bytes
  content_type: str | None = None
  description: str | None = None
  spoiler: bool = False

  @classmethod
  def text(
    cls,
    filename: str,
    text: str,
    *,
    description: str | None = None,
    spoiler: bool = False,
  ) -> Upload:
    """A text file (UTF-8) from a string."""
    return cls(
      filename, text.encode(), "text/plain; charset=utf-8", description, spoiler
    )

  @classmethod
  def json(
    cls,
    filename: str,
    value: JsonValue,
    *,
    description: str | None = None,
    spoiler: bool = False,
  ) -> Upload:
    """A JSON file from a value."""
    import json

    data = json.dumps(value, indent=2, ensure_ascii=False).encode()
    return cls(filename, data, "application/json", description, spoiler)

  @classmethod
  def from_path(
    cls,
    path: str | PathLike[str],
    *,
    filename: str | None = None,
    content_type: str | None = None,
    description: str | None = None,
    spoiler: bool = False,
  ) -> Upload:
    """A file read from disk now; named after the path unless `filename` is given."""
    from pathlib import Path

    source = Path(path)
    return cls(
      filename or source.name, source.read_bytes(), content_type, description, spoiler
    )

  @property
  def name(self) -> str:
    """The name it is sent under: `SPOILER_` is how Discord marks a spoiler."""
    return f"SPOILER_{self.filename}" if self.spoiler else self.filename

  @property
  def url(self) -> str:
    """`attachment://<name>`: how a message refers to a file sent with it."""
    return f"attachment://{self.name}"

  @property
  def size(self) -> int:
    """Its size in bytes."""
    return len(self.data)


type Media = str | Upload
"""A picture, video or file: a URL, or an `Upload` sent with the message."""


def _url(media: Media) -> str:
  return media.url if isinstance(media, Upload) else media


def _hidden(media: Media, spoiler: bool) -> bool:
  return spoiler or (isinstance(media, Upload) and media.spoiler)


EPHEMERAL = 1 << 6
SUPPRESS_EMBEDS = 1 << 2
SUPPRESS_NOTIFICATIONS = 1 << 12
IS_COMPONENTS_V2 = 1 << 15

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

  @overload
  def build[F: BuildMiddleware](self, function: F, /) -> F: ...
  @overload
  def build(
    self, /, *, only: Only = None
  ) -> Callable[[BuildMiddleware], BuildMiddleware]: ...

  def build(
    self, function: BuildMiddleware | None = None, /, *, only: Only = None
  ) -> Any:
    """Register construction middleware (a decorator, with or without `only=`)."""

    def register(function: BuildMiddleware) -> BuildMiddleware:
      self._build.append((function, only))
      return function

    return register if function is None else register(function)

  @overload
  def serialize[F: SerializeMiddleware](self, function: F, /) -> F: ...
  @overload
  def serialize(
    self, /, *, only: Only = None
  ) -> Callable[[SerializeMiddleware], SerializeMiddleware]: ...

  def serialize(
    self, function: SerializeMiddleware | None = None, /, *, only: Only = None
  ) -> Any:
    """Register serialization middleware (a decorator, with or without `only=`)."""

    def register(function: SerializeMiddleware) -> SerializeMiddleware:
      self._serialize.append((function, only))
      return function

    return register if function is None else register(function)

  def remove(self, function: BuildMiddleware | SerializeMiddleware) -> bool:
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


# What Discord says about each component ---------------------------------------------
#
# Limits are not repeated here: a component class declares its Discord type (`code`) and the
# metaclass reads its limits from Discord's generated request models when the class is
# created, so they cannot drift from what Discord enforces.

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


_model_cache: dict[Any, dict[str, tuple[int, int | None]]] = {}


def _limits_in(model: Any) -> dict[str, tuple[int, int | None]]:
  """`{field: (minimum, maximum)}` for a generated Discord model."""
  if model not in _model_cache:
    import typing

    import annotated_types

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
    _model_cache[model] = found
  return _model_cache[model]


_DECLARES = ("code", "main", "limits", "model")
"""What a component class declares in its body; the metaclass derives the rest from them."""


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
    cls = super().__new__(mcs, name, bases, namespace)
    derive = getattr(cls, "_derive", None)
    if derive is not None and any(k in namespace for k in _DECLARES):
      derive()  # fill in what the class's declarations imply (its limits, its `max`)
    return cls

  # Typed as returning the class's own instances, so type checkers ignore this
  # `__call__` and check arguments against each component's real `__init__`.
  def __call__[T](cls: type[T], *args: Any, **kwargs: Any) -> T:
    built: Any
    if not hooks._build or _building.get():  # pyright: ignore[reportPrivateUsage]
      built = super().__call__(*args, **kwargs)  # pyright: ignore[reportArgumentType]
    else:
      built = hooks.run_build(cls, args, kwargs)
    if isinstance(built, Component):
      built._accumulate()  # pyright: ignore[reportPrivateUsage]
    return cast(T, built)


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
  if isinstance(item, Component):
    return item.components_count, item.text_count
  if isinstance(item, str):  # a Section's plain-text shorthand is a Text Display
    return 1, utf16_length(item)
  if isinstance(item, Mapping):
    components, text = (
      1,
      utf16_length(item.get("content") or "") if item.get("type") == 10 else 0,
    )
    for child in item.get("components") or ():
      more, characters = _tally(child)
      components, text = components + more, text + characters
    if item.get("accessory"):
      more, characters = _tally(item["accessory"])
      components, text = components + more, text + characters
    return components, text
  return 1, 0


def message_measures(
  components: Buildable | Sequence[Buildable],
) -> tuple[Measure, ...]:
  """A message's totals against Discord's two message-wide limits."""
  items = (
    cast(Sequence[Buildable], components)
    if isinstance(components, list | tuple)
    else [components]
  )
  components_in_all = text_in_all = 0
  for item in items:
    more, characters = _tally(item)
    components_in_all, text_in_all = components_in_all + more, text_in_all + characters
  return (
    Measure("components in all", components_in_all, MAX_COMPONENTS),
    Measure("text in all", text_in_all, MAX_TEXT),
  )


class Component(metaclass=_Hooked):
  """The root of every message and modal component, version 1 and version 2 alike
  (`Button`, `ActionRow`, `TextDisplay`, `Container`, `TextInput`, ...).

  Every component knows its Discord JSON (`to_dict`), what it holds (`count`, `max`,
  `remaining`, `components_count`, `text_count`) and the limits it must stay within; the
  hooks (`micro.discord.ui.hooks`) run on all of them. `isinstance(x, Component)` is
  how to tell a builder from a plain dict."""

  __slots__ = ("components_count", "text_count")
  components_count: int
  """This component and everything inside it."""
  text_count: int
  """Characters of Text Display content inside it, in all."""
  slots: ClassVar[int] = 1
  """What it costs inside its parent's `count`: 1, but a select takes a whole row (5)."""
  code: ClassVar[int | None] = None
  """Discord's component type number, declared in the class body (None: no JSON of its own)."""
  main: ClassVar[str | int | None] = None
  """The main dimension `count` measures, declared in the class body: the name of the limit
  that bounds it (a field of Discord's model), or a number, or None if it has none."""
  limits: ClassVar[Mapping[str, tuple[int, int | None]]] = {}
  """`{field: (minimum, maximum)}`, read from Discord's own request models by the metaclass
  when the class is created (a class that is not in a model declares them itself). A
  subclass inherits them."""
  max: ClassVar[int | None] = None
  """The limit of `count` (None when unbounded): derived from `main` when the class is
  created. Read it on the class or an instance."""

  @classmethod
  def _derive(cls) -> None:
    """Called by the metaclass when a class declares `code`, `main` or `limits`."""
    if "limits" not in cls.__dict__:
      if cls.code is None:
        raise TypeError(f"{cls.__name__} declares neither `code` nor `limits`.")
      from micro.discord.models import http as models

      name = _MESSAGE_MODELS.get(cls.code) or _MODAL_MODELS[cls.code]
      cls.limits = _limits_in(getattr(models, name))
    if "max" not in cls.__dict__:
      main = cls.main
      cls.max = (
        main
        if isinstance(main, int)
        else None
        if main is None
        else cls.limits.get(main, (0, None))[1]
      )

  def _main(self) -> int:
    """How much of its main dimension it holds (`count`); 0 for one with none."""
    return 0

  @property
  def count(self) -> int:
    """How much of its main dimension it holds (see `max`): an action row's slots used,
    a section's texts, a gallery's items, a text's characters, a container's components."""
    return self._main()

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
    limits = self.limits
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


def utf16_length(text: str) -> int:
  """Length the way Discord counts text: UTF-16 code units, so 😀 is 2, not 1."""
  return len(text.encode("utf-16-le")) // 2


def _lengths(**fields: Any) -> dict[str, int]:
  """Size of each field that is set: text in UTF-16 units, lists by item count."""
  return {
    name: utf16_length(value) if isinstance(value, str) else len(value)
    for name, value in fields.items()
    if value is not None
  }


def check_limits(component: Any, next: Callable[[], Json]) -> Json:
  """Serialization middleware (registered by default): refuse a component over a limit.

  Remove it with `hooks.remove(check_limits)` to send what Discord would reject.
  """
  if isinstance(component, Component | Embed):
    enforce(component.measures, type(component).__name__)
  return next()


def _alt(media: Media, description: str | None) -> str | None:
  if description is None and isinstance(media, Upload):
    return media.description
  return description


def _put[D: Json](data: D, **items: JsonValue) -> D:
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


@dataclass(frozen=True, slots=True)
class EmbedField(metaclass=_Hooked):
  """One name and value in an embed; `inline` sets fields side by side."""

  name: str
  """The field's heading (up to 256 characters)."""
  value: str
  """Its text (up to 1024 characters)."""
  inline: bool = False
  """Show it beside the neighbouring inline fields."""

  def to_dict(self) -> Json:
    """This field as the JSON object Discord expects."""
    return {"name": self.name, "value": self.value, "inline": self.inline}


@dataclass(frozen=True, slots=True)
class EmbedFooter(metaclass=_Hooked):
  """Small text at the bottom of an embed, with an optional icon."""

  text: str
  """The footer text (up to 2048 characters)."""
  icon: Media | None = None
  """A small picture left of the text: a URL or an `Upload`."""

  def to_dict(self) -> Json:
    """This footer as the JSON object Discord expects."""
    return _put(
      {"text": self.text}, icon_url=None if self.icon is None else _url(self.icon)
    )


@dataclass(frozen=True, slots=True)
class EmbedAuthor(metaclass=_Hooked):
  """A name (that may link somewhere) with an icon, at the top of an embed."""

  name: str
  """The author's name (up to 256 characters)."""
  url: str | None = None
  """Where the name links to."""
  icon: Media | None = None
  """A small picture beside the name: a URL or an `Upload`."""

  def to_dict(self) -> Json:
    """This author as the JSON object Discord expects."""
    return _put(
      {"name": self.name},
      url=self.url,
      icon_url=None if self.icon is None else _url(self.icon),
    )


MAX_EMBEDS = 10
MAX_EMBED_TEXT = 6000
"""Characters of text all of a message's embeds may hold between them."""


@dataclass(frozen=True, slots=True)
class Embed(metaclass=_Hooked):
  """A rich embed. Every part is optional; a picture is a URL or an `Upload`, which the
  message then attaches by itself.

      Embed("Sales", "This week", colour=Colour.GREEN, image=chart,
            fields=[EmbedField("North", "12"), EmbedField("South", "9", inline=True)],
            footer=EmbedFooter("updated"), author=EmbedAuthor("Ada", icon=avatar_url))

  Embeds are immutable; `dataclasses.replace` gives a changed copy. The limits Discord enforces
  (256 title, 4096 description, 25 fields, 6000 characters over a message's embeds, ...)
  are checked when it is serialized (see `measures`).
  """

  model: ClassVar[str] = "RichEmbed"
  """The Discord request model its limits are read from (by the metaclass, when the class
  is created)."""
  limits: ClassVar[Mapping[str, tuple[int, int | None]]]
  """`{field: (minimum, maximum)}` of an embed, from `model`; a subclass inherits them."""
  field_limits: ClassVar[Mapping[str, tuple[int, int | None]]]
  """The same for one field of an embed (`RichEmbedField`)."""
  footer_limit: ClassVar[int | None]
  """The longest footer text (`RichEmbedFooter`)."""
  author_limit: ClassVar[int | None]
  """The longest author name (`RichEmbedAuthor`)."""

  @classmethod
  def _derive(cls) -> None:
    """Called by the metaclass when a class declares `model` or `limits`."""
    from micro.discord.models import http as models

    if "limits" not in cls.__dict__:
      cls.limits = _limits_in(getattr(models, cls.model))
    if "field_limits" not in cls.__dict__:
      cls.field_limits = _limits_in(models.RichEmbedField)
    if "footer_limit" not in cls.__dict__:
      cls.footer_limit = _limits_in(models.RichEmbedFooter)["text"][1]
    if "author_limit" not in cls.__dict__:
      cls.author_limit = _limits_in(models.RichEmbedAuthor)["name"][1]

  title: str | None
  """The heading (up to 256 characters)."""
  description: str | None
  """The body text (up to 4096 characters)."""
  colour: Colour | None
  """The coloured bar down the left edge (a `Colour`)."""
  url: str | None
  """Where the title links to."""
  fields: tuple[EmbedField, ...]
  """Name and value pairs below the description (up to 25)."""
  footer: EmbedFooter | None
  """Small text at the bottom."""
  image: Media | None
  """A large picture: a URL or an `Upload`."""
  thumbnail: Media | None
  """A small picture at the top right: a URL or an `Upload`."""
  author: EmbedAuthor | None
  """A name with an icon above the title."""
  timestamp: datetime | None
  """A time shown beside the footer."""

  def __init__(
    self,
    title: str | None = None,
    description: str | None = None,
    *,
    colour: ColourLike | None = None,
    url: str | None = None,
    fields: Sequence[EmbedField] = (),
    footer: EmbedFooter | None = None,
    image: Media | None = None,
    thumbnail: Media | None = None,
    author: EmbedAuthor | None = None,
    timestamp: datetime | None = None,
  ) -> None:
    set_ = object.__setattr__
    set_(self, "title", title)
    set_(self, "description", description)
    set_(self, "colour", None if colour is None else Colour.parse(colour))
    set_(self, "url", url)
    set_(self, "fields", tuple(fields))
    set_(self, "footer", footer)
    set_(self, "image", image)
    set_(self, "thumbnail", thumbnail)
    set_(self, "author", author)
    set_(self, "timestamp", timestamp)

  @property
  def uploads(self) -> tuple[Upload, ...]:
    """The `Upload`s this embed shows."""
    shown = (
      self.image,
      self.thumbnail,
      self.footer.icon if self.footer else None,
      self.author.icon if self.author else None,
    )
    return tuple(item for item in shown if isinstance(item, Upload))

  @property
  def length(self) -> int:
    """Characters of text Discord counts toward the 6000 an embed (all of a message's
    embeds, together) may hold: title, description, field names and values, footer and
    author names; in UTF-16 units."""
    return embed_length(self._json())

  @property
  def measures(self) -> tuple[Measure, ...]:
    """Every count this embed has, with Discord's limit for it."""
    top, name = self.limits, self.field_limits
    value = name["value"][1]
    found = [
      Measure("title", utf16_length(self.title or ""), top["title"][1]),
      Measure(
        "description", utf16_length(self.description or ""), top["description"][1]
      ),
      Measure("fields", len(self.fields), top["fields"][1]),
      Measure("text in all", self.length, MAX_EMBED_TEXT),
    ]
    for index, item in enumerate(self.fields, 1):
      found.append(
        Measure(f"field {index} name", utf16_length(item.name), name["name"][1], 1)
      )
      found.append(Measure(f"field {index} value", utf16_length(item.value), value, 1))
    if self.footer is not None:
      found.append(Measure("footer", utf16_length(self.footer.text), self.footer_limit))
    if self.author is not None:
      found.append(Measure("author", utf16_length(self.author.name), self.author_limit))
    return tuple(found)

  def to_dict(self) -> Json:
    """This embed as the JSON object Discord expects."""
    return self._json()

  def _json(self) -> Json:
    value: Json = {}
    _put(
      value,
      title=self.title,
      description=self.description,
      color=None if self.colour is None else int(self.colour),  # Discord's key
      url=self.url,
    )
    if self.timestamp is not None:
      value["timestamp"] = self.timestamp.isoformat()
    if self.fields:
      value["fields"] = [item.to_dict() for item in self.fields]
    if self.footer is not None:
      value["footer"] = self.footer.to_dict()
    if self.image is not None:
      value["image"] = {"url": _url(self.image)}
    if self.thumbnail is not None:
      value["thumbnail"] = {"url": _url(self.thumbnail)}
    if self.author is not None:
      value["author"] = self.author.to_dict()
    return value


def embed_length(embed: Mapping[str, JsonValue]) -> int:
  """The characters of an embed (as Discord's JSON) that count toward the 6000 limit."""
  total = 0

  def text(value: JsonValue) -> int:
    return utf16_length(value) if isinstance(value, str) else 0

  def part(name: str, key: str) -> int:
    inner = embed.get(name)
    return text(inner.get(key)) if isinstance(inner, Mapping) else 0

  total += text(embed.get("title")) + text(embed.get("description"))
  total += part("footer", "text") + part("author", "name")
  fields = embed.get("fields")
  for item in fields if isinstance(fields, list) else ():
    if isinstance(item, Mapping):
      total += text(item.get("name")) + text(item.get("value"))
  return total


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


def _emoji(value: Emoji | None) -> Json | None:
  return None if value is None else value.to_dict()


# Buttons and selects -----------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Button(Component):
  """A button: `custom_id` (an interaction), `url` (a link), or `sku_id` (premium)."""

  label: str | None = None
  """The text on the button (up to 80 characters)."""
  custom_id: str | None = None
  """What identifies this button when it is clicked (`interaction.custom_id`). Exactly one of `custom_id`, `url` and `sku_id`."""
  url: str | None = None
  """Makes a link button that opens this address (no interaction is sent)."""
  style: ButtonStyle = ButtonStyle.PRIMARY
  """How it looks (`ButtonStyle`); a `url` always makes it `LINK` and a `sku_id` `PREMIUM`."""
  emoji: Emoji | None = None
  """An `Emoji` shown before the label."""
  disabled: bool = False
  """Show it greyed out and unclickable."""
  sku_id: int | str | None = None
  """Makes a premium purchase button for this SKU (it then has no label or emoji)."""
  id: int | None = None
  """A number you give it to find it in a layout message later."""

  def __post_init__(self) -> None:
    targets = [x for x in (self.custom_id, self.url, self.sku_id) if x is not None]
    if len(targets) != 1:
      raise ValueError("A button needs exactly one of custom_id, url or sku_id.")
    if self.sku_id is not None and (self.label is not None or self.emoji is not None):
      raise ValueError("A premium button has no label or emoji.")

  def to_dict(self) -> Json:
    """This component as the JSON object Discord expects."""
    style = (
      ButtonStyle.PREMIUM
      if self.sku_id is not None
      else ButtonStyle.LINK
      if self.url
      else self.style
    )
    value: Json = {"type": 2, "style": int(style), "disabled": self.disabled}
    _put(value, id=self.id, label=self.label, custom_id=self.custom_id, url=self.url)
    if self.sku_id is not None:
      value["sku_id"] = str(self.sku_id)
    _put(value, emoji=_emoji(self.emoji))
    return value

  code = 2
  main = "label"

  def _main(self) -> int:
    return utf16_length(self.label or "")

  def _counts(self) -> Mapping[str, int]:
    return _lengths(label=self.label, custom_id=self.custom_id)


@dataclass(frozen=True, slots=True)
class SelectOption(metaclass=_Hooked):
  """One option of a string select. Its `value` (what a submission reports) is its
  `label` unless you give one."""

  label: str
  """What the person sees (up to 100 characters)."""
  value: str
  """What a submission reports for this option."""
  description: str | None = None
  """A line of smaller text under the label."""
  default: bool = False
  """Whether it is selected to begin with."""
  emoji: Emoji | None = None
  """An `Emoji` shown before the label."""

  def __init__(
    self,
    label: str,
    value: str | None = None,
    description: str | None = None,
    default: bool = False,
    emoji: Emoji | None = None,
  ) -> None:
    set_ = object.__setattr__
    set_(self, "label", label)
    set_(self, "value", label if value is None else value)
    set_(self, "description", description)
    set_(self, "default", default)
    set_(self, "emoji", emoji)

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
class StringSelect(Component):
  """A menu of `SelectOption`s."""

  custom_id: str
  """What identifies this menu when it is used (`interaction.custom_id`)."""
  options: Sequence[SelectOption]
  """The choices (up to 25)."""
  placeholder: str | None = None
  """Text shown while nothing is chosen."""
  min_values: int | None = None
  """The fewest options that must be chosen."""
  max_values: int | None = None
  """The most options that may be chosen."""
  disabled: bool = False
  """Show it greyed out."""
  required: bool | None = None
  """Whether it must be filled in (modals only)."""
  id: int | None = None
  """A number you give it to find it in a layout message later."""

  def to_dict(self) -> Json:
    """This component as the JSON object Discord expects."""
    return _select(
      3, self.custom_id, self.placeholder, self.min_values, self.max_values,
      self.disabled, self.required, self.id,
      options=[o.to_dict() for o in self.options],
    )  # fmt: skip

  code = 3
  main = "options"
  slots = 5

  def _main(self) -> int:
    return len(self.options)

  def _counts(self) -> Mapping[str, int]:
    return _lengths(
      custom_id=self.custom_id, options=self.options, placeholder=self.placeholder
    )


Select = StringSelect
"""The older name for `StringSelect`."""


@dataclass(frozen=True, slots=True)
class UserSelect(Component):
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

  code = 5
  main = "default_values"
  slots = 5

  def _main(self) -> int:
    return len(self.defaults or ())

  def _counts(self) -> Mapping[str, int]:
    return _lengths(
      custom_id=self.custom_id,
      placeholder=self.placeholder,
      default_values=self.defaults,
    )


@dataclass(frozen=True, slots=True)
class RoleSelect(Component):
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

  code = 6
  main = "default_values"
  slots = 5

  def _main(self) -> int:
    return len(self.defaults or ())

  def _counts(self) -> Mapping[str, int]:
    return _lengths(
      custom_id=self.custom_id,
      placeholder=self.placeholder,
      default_values=self.defaults,
    )


@dataclass(frozen=True, slots=True)
class MentionableSelect(Component):
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

  code = 7
  main = "default_values"
  slots = 5

  def _main(self) -> int:
    return len(self.defaults or ())

  def _counts(self) -> Mapping[str, int]:
    return _lengths(
      custom_id=self.custom_id,
      placeholder=self.placeholder,
      default_values=self.defaults,
    )


@dataclass(frozen=True, slots=True)
class ChannelSelect(Component):
  """Channels; `channel_types` limits them (`ChannelType.GUILD_TEXT`, ...)."""

  custom_id: str
  placeholder: str | None = None
  min_values: int | None = None
  max_values: int | None = None
  disabled: bool = False
  required: bool | None = None
  channel_types: Sequence[ChannelType] = ()
  defaults: Sequence[int | str | Default] = ()
  id: int | None = None

  def to_dict(self) -> Json:
    """This component as the JSON object Discord expects."""
    kinds = [int(kind) for kind in self.channel_types]
    return _select(
      8, self.custom_id, self.placeholder, self.min_values, self.max_values,
      self.disabled, self.required, self.id,
      channel_types=kinds or None,
      default_values=_defaults("channel", self.defaults) or None,
    )  # fmt: skip

  code = 8
  main = "default_values"
  slots = 5

  def _main(self) -> int:
    return len(self.defaults or ())

  def _counts(self) -> Mapping[str, int]:
    return _lengths(
      custom_id=self.custom_id,
      placeholder=self.placeholder,
      default_values=self.defaults,
    )


type Select_ = (
  StringSelect | UserSelect | RoleSelect | MentionableSelect | ChannelSelect
)
_SELECTS = (StringSelect, UserSelect, RoleSelect, MentionableSelect, ChannelSelect)
type Interactive = Button | Select_
"""What goes in an action row: a button or a select menu."""


@dataclass(frozen=True, slots=True)
class ActionRow(Component):
  """Up to five buttons, or one select."""

  components: Sequence[Interactive]
  id: int | None = None

  def __init__(self, *components: Interactive, id: int | None = None) -> None:
    object.__setattr__(self, "components", tuple(components))
    object.__setattr__(self, "id", id)

  def to_dict(self) -> Json:
    """This component as the JSON object Discord expects."""
    return _put(
      {"type": 1, "components": [c.to_dict() for c in self.components]}, id=self.id
    )

  code = 1
  main = "components"

  def _main(self) -> int:
    return sum(_slots(item) for item in self.components)

  def _children(self) -> Iterable[Any]:
    return self.components

  def _counts(self) -> Mapping[str, int]:
    return {"components": sum(_slots(item) for item in self.components)}


# Layout components (v2) ---------------------------------------------------------


@dataclass(frozen=True, slots=True)
class TextDisplay(Component):
  """Markdown text. Counts toward the message's 4000 characters of text in total."""

  content: str
  """The Markdown text."""
  id: int | None = None
  """A number you give it to find it in a layout later."""

  def to_dict(self) -> Json:
    """This component as the JSON object Discord expects."""
    return _put({"type": 10, "content": self.content}, id=self.id)

  code = 10
  main = "content"

  def _main(self) -> int:
    return utf16_length(self.content)

  def _text(self) -> int:
    return utf16_length(self.content)

  def _counts(self) -> Mapping[str, int]:
    return {"content": utf16_length(self.content)}


@dataclass(frozen=True, slots=True)
class Thumbnail(Component):
  """A small image beside text: only as a `Section` accessory.

  `media` is a URL or an `Upload` (attached by the message itself).
  """

  media: Media
  description: str | None = None
  spoiler: bool = False
  id: int | None = None

  @property
  def url(self) -> str:
    """The picture's URL (`attachment://name` for an `Upload`)."""
    return _url(self.media)

  def to_dict(self) -> Json:
    """This component as the JSON object Discord expects."""
    value: Json = {
      "type": 11,
      "media": {"url": self.url},
      "spoiler": _hidden(self.media, self.spoiler),
    }
    return _put(value, id=self.id, description=_alt(self.media, self.description))

  code = 11
  main = "description"

  def _main(self) -> int:
    return utf16_length(self.description or "")

  def _counts(self) -> Mapping[str, int]:
    return _lengths(description=self.description)


@dataclass(frozen=True, slots=True)
class Section(Component):
  """One to three texts with a `Button` or `Thumbnail` beside them."""

  texts: Sequence[TextDisplay]
  """One to three `TextDisplay`s."""
  accessory: Button | Thumbnail
  """A `Button` or `Thumbnail` shown beside the texts."""
  id: int | None = None
  """A number you give it to find it in a layout later."""

  def __init__(
    self,
    *texts: TextDisplay,
    accessory: Button | Thumbnail,
    id: int | None = None,
  ) -> None:
    object.__setattr__(self, "texts", tuple(texts))
    object.__setattr__(self, "accessory", accessory)
    object.__setattr__(self, "id", id)

  def to_dict(self) -> Json:
    """This component as the JSON object Discord expects."""
    value: Json = {
      "type": 9,
      "components": [t.to_dict() for t in self.texts],
      "accessory": self.accessory.to_dict(),
    }
    return _put(value, id=self.id)

  code = 9
  main = "components"

  def _main(self) -> int:
    return len(self.texts)

  def _children(self) -> Iterable[Any]:
    return (*self.texts, self.accessory)

  def _counts(self) -> Mapping[str, int]:
    return {"components": len(self.texts)}


@dataclass(frozen=True, slots=True)
class MediaItem(metaclass=_Hooked):
  """One picture or video of a `MediaGallery`: a URL or an `Upload`."""

  media: Media
  description: str | None = None
  spoiler: bool = False

  @property
  def url(self) -> str:
    """The item's URL (`attachment://name` for an `Upload`)."""
    return _url(self.media)

  def to_dict(self) -> Json:
    """This component as the JSON object Discord expects."""
    value: Json = {
      "media": {"url": self.url},
      "spoiler": _hidden(self.media, self.spoiler),
    }
    return _put(value, description=_alt(self.media, self.description))


@dataclass(frozen=True, slots=True)
class MediaGallery(Component):
  """Up to ten pictures or videos."""

  items: Sequence[MediaItem]
  id: int | None = None

  def __init__(self, *items: MediaItem, id: int | None = None) -> None:
    object.__setattr__(self, "items", tuple(items))
    object.__setattr__(self, "id", id)

  def to_dict(self) -> Json:
    """This component as the JSON object Discord expects."""
    return _put({"type": 12, "items": [i.to_dict() for i in self.items]}, id=self.id)

  code = 12
  main = "items"

  def _main(self) -> int:
    return len(self.items)

  def _counts(self) -> Mapping[str, int]:
    return {"items": len(self.items)}


@dataclass(frozen=True, slots=True)
class File(Component):
  """A file shown in the message: an `Upload`, or `attachment://name` for one
  sent in `files=` (Discord shows only attached files this way, not other URLs)."""

  file: Media
  spoiler: bool = False
  id: int | None = None

  def __post_init__(self) -> None:
    if not self.url.startswith("attachment://"):
      raise ValueError(
        "A File component shows an attached file: give it an Upload, or "
        "attachment://name."
      )

  @property
  def url(self) -> str:
    """`attachment://name`."""
    return _url(self.file)

  def to_dict(self) -> Json:
    """This component as the JSON object Discord expects."""
    value: Json = {
      "type": 13,
      "file": {"url": self.url},
      "spoiler": _hidden(self.file, self.spoiler),
    }
    return _put(value, id=self.id)

  code = 13
  main = None


@dataclass(frozen=True, slots=True)
class Separator(Component):
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

  code = 14
  main = None


type ContainerChild = (
  Interactive
  | ActionRow
  | TextDisplay
  | Section
  | MediaGallery
  | File
  | Separator
  | Mapping[str, JsonValue]
)
"""Anything that can sit inside a `Container`; a plain dict is passed through."""


@dataclass(frozen=True, slots=True)
class Container(Component):
  """A bordered box of components with an optional accent colour."""

  components: Sequence[ContainerChild]
  accent_colour: Colour | None = None
  """The coloured bar down the left edge (a `Colour`)."""
  spoiler: bool = False
  """Hide it behind a spoiler."""
  id: int | None = None
  """A number you give it to find it in a layout later."""

  def __init__(
    self,
    *components: ContainerChild,
    accent_colour: ColourLike | None = None,
    spoiler: bool = False,
    id: int | None = None,
  ) -> None:
    object.__setattr__(self, "components", tuple(components))
    object.__setattr__(
      self,
      "accent_colour",
      None if accent_colour is None else Colour.parse(accent_colour),
    )
    object.__setattr__(self, "spoiler", spoiler)
    object.__setattr__(self, "id", id)

  def to_dict(self) -> Json:
    """This component as the JSON object Discord expects."""
    value: Json = {
      "type": 17,
      "components": list(rows(self.components)),
      "spoiler": self.spoiler,
    }
    return _put(
      value,
      id=self.id,
      accent_color=None if self.accent_colour is None else int(self.accent_colour),
    )  # Discord's key

  code = 17
  main = MAX_COMPONENTS

  def _main(self) -> int:
    return self.components_count

  def _children(self) -> Iterable[Any]:
    return self.components

  def _counts(self) -> Mapping[str, int]:
    return {"components": len(self.components)}


_LAYOUT = (TextDisplay, Section, Thumbnail, MediaGallery, File, Separator, Container)
type Buildable = ContainerChild | Container
"""Anything that can be a top-level component of a message."""


def rows(components: Sequence[Buildable]) -> list[Json]:
  """Lay out components: loose buttons fill rows of five, loose selects get a row.

  Rows and layout components stay as they are; a plain dict passes through.
  """
  laid_out: list[Json] = []
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


def is_v2(components: Sequence[Buildable] | None) -> bool:
  """Whether a message's components use the layout set (so it is a v2 message)."""
  return any(
    isinstance(item, _LAYOUT)
    or (isinstance(item, Mapping) and item.get("type") in (9, 10, 11, 12, 13, 14, 17))
    for item in components or ()
  )


# Modal components ---------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class TextInput(Component):
  """A text field. In a `Label`, leave `label` out; bare in a `Modal`, it needs one."""

  custom_id: str
  """What identifies this field in the submission (`interaction.submitted.fields[custom_id]`)."""
  label: str | None = None
  """The field's heading; leave it out inside a `Label`."""
  style: TextInputStyle = TextInputStyle.SHORT
  """One line (`SHORT`) or several (`PARAGRAPH`)."""
  required: bool = True
  """Whether it must be filled in."""
  placeholder: str | None = None
  """Hint text shown while empty."""
  value: str | None = None
  """Text it starts with."""
  min_length: int | None = None
  """The fewest characters accepted."""
  max_length: int | None = None
  """The most characters accepted."""
  id: int | None = None
  """A number you give it to find it in a layout later."""

  def to_dict(self) -> Json:
    """This component as the JSON object Discord expects."""
    data: Json = {
      "type": 4,
      "custom_id": self.custom_id,
      "style": int(self.style),
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

  code = 4
  main = "value"

  def _main(self) -> int:
    return utf16_length(self.value or "")

  def _counts(self) -> Mapping[str, int]:
    return _lengths(
      custom_id=self.custom_id,
      label=self.label,
      value=self.value,
      placeholder=self.placeholder,
    )


@dataclass(frozen=True, slots=True)
class GroupOption(metaclass=_Hooked):
  """An option of a `RadioGroup` or `CheckboxGroup`. Its `value` is its `label` unless
  you give one."""

  label: str
  value: str
  description: str | None = None
  default: bool = False

  def __init__(
    self,
    label: str,
    value: str | None = None,
    description: str | None = None,
    default: bool = False,
  ) -> None:
    set_ = object.__setattr__
    set_(self, "label", label)
    set_(self, "value", label if value is None else value)
    set_(self, "description", description)
    set_(self, "default", default)

  def to_dict(self) -> Json:
    """This component as the JSON object Discord expects."""
    value: Json = {"label": self.label, "value": self.value, "default": self.default}
    return _put(value, description=self.description)


def _group(options: Sequence[GroupOption]) -> list[JsonValue]:
  return [option.to_dict() for option in options]


@dataclass(frozen=True, slots=True)
class RadioGroup(Component):
  """Pick exactly one of two to ten options."""

  custom_id: str
  options: Sequence[GroupOption]
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

  code = 21
  main = "options"

  def _main(self) -> int:
    return len(self.options)

  def _counts(self) -> Mapping[str, int]:
    return _lengths(custom_id=self.custom_id, options=self.options)


@dataclass(frozen=True, slots=True)
class CheckboxGroup(Component):
  """Pick any of up to ten options (`min_values`, `max_values` limit how many)."""

  custom_id: str
  options: Sequence[GroupOption]
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

  code = 22
  main = "options"

  def _main(self) -> int:
    return len(self.options)

  def _counts(self) -> Mapping[str, int]:
    return _lengths(custom_id=self.custom_id, options=self.options)


@dataclass(frozen=True, slots=True)
class Checkbox(Component):
  """A single yes/no box."""

  custom_id: str
  default: bool | None = None
  id: int | None = None

  def to_dict(self) -> Json:
    """This component as the JSON object Discord expects."""
    return _put(
      {"type": 23, "custom_id": self.custom_id}, id=self.id, default=self.default
    )

  code = 23
  main = None

  def _counts(self) -> Mapping[str, int]:
    return _lengths(custom_id=self.custom_id)


@dataclass(frozen=True, slots=True)
class FileUpload(Component):
  """Ask for files; read them with `interaction.attachments` after the submission."""

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

  code = 19
  main = None

  def _counts(self) -> Mapping[str, int]:
    return _lengths(custom_id=self.custom_id)


type ModalInput = (
  TextInput | Select_ | RadioGroup | CheckboxGroup | Checkbox | FileUpload
)


@dataclass(frozen=True, slots=True)
class Label(Component):
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

  code = 18
  main = "label"

  def _main(self) -> int:
    return utf16_length(self.label)

  def _children(self) -> Iterable[Any]:
    return (self.component,)

  def _counts(self) -> Mapping[str, int]:
    return _lengths(label=self.label, description=self.description)


@dataclass(frozen=True, slots=True)
class Modal(Component):
  """A pop-up form of up to five `Label`s and `TextDisplay`s.

  A bare `TextInput` (with a label) is still accepted and sent in the older way.
  """

  custom_id: str
  """What `interaction.custom_id` is when the form is submitted."""
  title: str
  """The pop-up's heading (up to 45 characters)."""
  components: Sequence[Label | TextDisplay | TextInput | Mapping[str, JsonValue]] = (
    field(default_factory=tuple)
  )

  @property
  def inputs(
    self,
  ) -> Sequence[Label | TextDisplay | TextInput | Mapping[str, JsonValue]]:
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

  limits: ClassVar[Mapping[str, tuple[int, int | None]]] = {
    "title": (1, 45),
    "custom_id": (1, 100),
    "components": (1, 5),
  }
  """Not in one of Discord's models, so declared here."""
  main = "components"

  def _main(self) -> int:
    return len(self.components)

  def _children(self) -> Iterable[Any]:
    return self.components

  def _counts(self) -> Mapping[str, int]:
    return {
      "title": utf16_length(self.title),
      "custom_id": utf16_length(self.custom_id),
      "components": len(self.components),
    }


# Messages -----------------------------------------------------------------------


def message_body(
  content: str | None = None,
  *,
  embeds: Sequence[Embed | Json] = (),
  components: Sequence[Buildable] | None = None,
  allowed_mentions: AllowedMentions | None = None,
  ephemeral: bool = False,
  flags: int = 0,
  files: Sequence[Upload] = (),
) -> Json:
  """A message payload with safe mention defaults.

  Layout components set IS_COMPONENTS_V2, and such a message has no `content` or
  `embeds` (Discord rejects both). `files` are the uploads sent alongside (see
  `uploads_in`); they add the `attachments` list that carries their alt text.
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
    written = [item.to_dict() if isinstance(item, Embed) else item for item in embeds]
    enforce(
      (
        Measure("embeds", len(written), MAX_EMBEDS),
        Measure("text in all embeds", sum(map(embed_length, written)), MAX_EMBED_TEXT),
      ),
      "This message",
    )
    body["embeds"] = list(written)
  if components is not None:
    laid_out = rows(components)
    body["components"] = list(laid_out)
    enforce(message_measures(laid_out), "This message")
  if ephemeral:
    flags |= EPHEMERAL
  if flags:
    body["flags"] = flags
  if any(file.description for file in files):
    body["attachments"] = attachments(files)
  return body


@dataclass(frozen=True, slots=True)
class Draft(metaclass=_Hooked):
  """A message as data: what to say, with everything that goes with it.

      reply = Draft(
        "Report ready",
        embeds=[Embed("Sales", image=chart)],
        components=[Button("Open", custom_id="report.open")],
        ephemeral=True,
      )
      await interaction.respond(reply)              # also channel.send(reply), message.edit(reply)
      await interaction.respond(replace(reply, content="again"))

  A `Draft` is immutable and comparable, so build it anywhere (a helper, a template, a
  test) and send it wherever; nothing is sent until you do. Change one with
  `dataclasses.replace`. Every way of sending a message takes a `Draft` (or a plain
  string for a text-only one).

  For an edit, a part that is `None` is left as it is on the message and an empty one
  clears it: `Draft(embeds=())` removes the embeds, `Draft(content="")` the text. Files
  you add are added; `keep=[...]` lists the existing attachments that stay (`keep=[]`
  removes them all).
  Layout components make it a components v2 message, which has no `content` or
  `embeds`. `to_dict()` is the JSON Discord expects (and runs the serialize hooks).
  """

  content: str | None
  """The message text (up to 2000 characters). On an edit, `None` leaves it as it is and `""` clears it."""
  embeds: tuple[Embed | Json, ...] | None
  """Embeds to show (up to 10). On an edit, `None` leaves them and `()` removes them."""
  components: tuple[Buildable, ...] | None
  """Buttons, selects or layout components. On an edit, `None` leaves them and `()` removes them."""
  files: tuple[Upload, ...]
  """Files to upload with the message (`Upload`)."""
  allowed_mentions: AllowedMentions | None
  """Who the message may ping; leave it out for the safe default (see `AllowedMentions`)."""
  ephemeral: bool
  """Only the person who triggered the interaction sees it (interaction replies only)."""
  reply_to: int | str | None
  """The id of a message this one replies to."""
  tts: bool
  """Read the message aloud with text to speech."""
  silent: bool
  """Send without notifying anyone."""
  suppress_embeds: bool
  """Hide the link previews Discord would add."""
  keep: tuple[str, ...] | None
  """On an edit, the existing attachments (ids) that stay; `None` leaves them all, `()` removes them all."""

  def __init__(
    self,
    content: str | None = None,
    *,
    embeds: Sequence[Embed | Json] | None = None,
    components: Sequence[Buildable] | None = None,
    files: Sequence[Upload] = (),
    allowed_mentions: AllowedMentions | None = None,
    ephemeral: bool = False,
    reply_to: int | str | None = None,
    tts: bool = False,
    silent: bool = False,
    suppress_embeds: bool = False,
    keep: Sequence[Object | str | int] | None = None,
  ) -> None:
    from .objects import Object

    set_ = object.__setattr__
    set_(self, "content", content)
    set_(self, "embeds", None if embeds is None else tuple(embeds))
    set_(self, "components", None if components is None else tuple(components))
    set_(self, "files", tuple(files))
    set_(self, "allowed_mentions", allowed_mentions)
    set_(self, "ephemeral", ephemeral)
    set_(self, "reply_to", reply_to)
    set_(self, "tts", tts)
    set_(self, "silent", silent)
    set_(self, "suppress_embeds", suppress_embeds)
    set_(
      self,
      "keep",
      None
      if keep is None
      else tuple(item.id if isinstance(item, Object) else str(item) for item in keep),
    )

  @classmethod
  def of(cls, message: Draft | str | None) -> Draft:
    """The `Draft` for what a send method was given: itself, or a text-only one."""
    return message if isinstance(message, Draft) else cls(message)

  @property
  def uploads(self) -> tuple[Upload, ...]:
    """Every file this message sends: `files`, then those its embeds and components show."""
    return uploads_in(
      files=self.files, embeds=self.embeds or (), components=self.components
    )

  def to_dict(self) -> Json:
    """This message as the JSON Discord expects (without the files, which travel as
    separate parts: see `uploads`)."""
    flags = (SUPPRESS_NOTIFICATIONS if self.silent else 0) | (
      SUPPRESS_EMBEDS if self.suppress_embeds else 0
    )
    body = message_body(
      self.content,
      embeds=self.embeds or (),
      components=self.components,
      allowed_mentions=self.allowed_mentions,
      ephemeral=self.ephemeral,
      flags=flags,
      files=self.uploads,
    )
    if self.embeds is not None and not self.embeds:
      body["embeds"] = []  # an empty list clears them on an edit
    if self.reply_to is not None:
      body["message_reference"] = {
        "message_id": str(self.reply_to),
        "fail_if_not_exists": False,
      }
    if self.tts:
      body["tts"] = True
    if self.keep is not None:
      # Listing attachments replaces the message's files with exactly these.
      body["attachments"] = attachments(self.uploads, self.keep)
    return body


def uploads_in(
  *,
  files: Sequence[Upload] = (),
  embeds: Sequence[Embed | Json] = (),
  components: Sequence[Buildable] | None = None,
) -> tuple[Upload, ...]:
  """Every file a message sends: `files`, then the `Upload`s its embeds and
  components show, each once. Two different files under one name is a ValueError,
  since `attachment://name` could then mean either."""
  found: dict[str, Upload] = {}

  def add(upload: Upload) -> None:
    known = found.setdefault(upload.name, upload)
    if known is not upload and known != upload:
      raise ValueError(f"Two different files are both named {upload.name!r}.")

  def walk(item: object) -> None:
    if isinstance(item, Upload):
      add(item)
    elif isinstance(item, Thumbnail | MediaItem):
      walk(item.media)
    elif isinstance(item, File):
      walk(item.file)
    elif isinstance(item, MediaGallery):
      for inner in item.items:
        walk(inner)
    elif isinstance(item, Section):
      walk(item.accessory)
    elif isinstance(item, Container):
      for inner in item.components:
        walk(inner)

  for upload in files:
    add(upload)
  for item in embeds:
    if isinstance(item, Embed):
      for upload in item.uploads:
        add(upload)
  for item in components or ():
    walk(item)
  return tuple(found.values())


def attachments(
  files: Sequence[Upload], keep: Sequence[str | int] | None = None
) -> list[JsonValue]:
  """Discord's `attachments` list for a message: the files sent with it (by their
  position, with their alt text) after the ids of existing ones to `keep`."""
  listed: list[JsonValue] = [{"id": str(item)} for item in keep or ()]
  for index, file in enumerate(files):
    listed.append(
      _put({"id": str(index), "filename": file.name}, description=file.description)
    )
  return listed


# Validation ---------------------------------------------------------------------


def validate(
  components: Buildable | Sequence[Buildable], *, modal: bool = False
) -> None:
  """Check components against Discord's request models; ValueError if one is wrong.

  Accepts a builder, a dict, or a list of either; `modal=True` checks modal rules.
  """
  from pydantic import ValidationError

  from micro.discord.models import http as models

  table = _MODAL_MODELS if modal else _MESSAGE_MODELS
  items: Sequence[Buildable] = (
    cast(Sequence[Buildable], components)
    if isinstance(components, list | tuple)
    else [cast(Buildable, components)]
  )
  if not modal:
    enforce(message_measures(items), "This message")
  for item in items:
    payload: Mapping[str, JsonValue] = (
      item if isinstance(item, Mapping) else item.to_dict()
    )
    name = table.get(cast(int, payload.get("type", -1)))
    if name is None:
      raise ValueError(f"Component type {payload.get('type')!r} is not valid here.")
    try:
      getattr(models, name).model_validate(payload)
    except ValidationError as error:
      problems = "; ".join(
        f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in error.errors()[:3]
      )
      raise ValueError(f"{name}: {problems}") from error


hooks.serialize(check_limits)  # the limits are checked as components are serialized
