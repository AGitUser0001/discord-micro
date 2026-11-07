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
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

type Json = dict[str, Any]

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


def _put(data: Json, **items: Any) -> Json:
  """Add the items that are not None."""
  for key, item in items.items():
    if item is not None:
      data[key] = item
  return data


# Mentions and embeds -----------------------------------------------------------


@dataclass(frozen=True, slots=True)
class AllowedMentions:
  """Which mentions in a message may ping. Micro defaults to `none()`."""

  parse: tuple[Literal["users", "roles", "everyone"], ...] = ()
  users: tuple[int, ...] = ()
  roles: tuple[int, ...] = ()
  replied_user: bool = False

  @classmethod
  def none(cls) -> AllowedMentions:
    return cls()

  @classmethod
  def everything(cls) -> AllowedMentions:
    return cls(parse=("users", "roles", "everyone"), replied_user=True)

  @classmethod
  def only(
    cls, *, users: Iterable[int] = (), roles: Iterable[int] = ()
  ) -> AllowedMentions:
    return cls(users=tuple(users), roles=tuple(roles))

  def to_dict(self) -> Json:
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
class Emoji:
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
class Button:
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
    kind = "premium" if self.sku_id is not None else "link" if self.url else self.style
    value: Json = {"type": 2, "style": _BUTTON_STYLES[kind], "disabled": self.disabled}
    _put(value, id=self.id, label=self.label, custom_id=self.custom_id, url=self.url)
    if self.sku_id is not None:
      value["sku_id"] = str(self.sku_id)
    _put(value, emoji=_emoji(self.emoji))
    return value


@dataclass(frozen=True, slots=True)
class SelectOption:
  label: str
  value: str
  description: str | None = None
  default: bool = False
  emoji: str | Emoji | None = None

  def to_dict(self) -> Json:
    value: Json = {"label": self.label, "value": self.value, "default": self.default}
    return _put(value, description=self.description, emoji=_emoji(self.emoji))


@dataclass(frozen=True, slots=True)
class Default:
  """A preselected entry of a user, role, mentionable or channel select."""

  type: Literal["user", "role", "channel"]
  id: int | str

  @classmethod
  def user(cls, id: int | str) -> Default:
    return cls("user", id)

  @classmethod
  def role(cls, id: int | str) -> Default:
    return cls("role", id)

  @classmethod
  def channel(cls, id: int | str) -> Default:
    return cls("channel", id)

  def to_dict(self) -> Json:
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
class StringSelect:
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
class UserSelect:
  custom_id: str
  placeholder: str | None = None
  min_values: int | None = None
  max_values: int | None = None
  disabled: bool = False
  required: bool | None = None
  defaults: Sequence[int | str | Default] = ()
  id: int | None = None

  def to_dict(self) -> Json:
    return _select(
      5, self.custom_id, self.placeholder, self.min_values, self.max_values,
      self.disabled, self.required, self.id,
      default_values=_defaults("user", self.defaults) or None,
    )  # fmt: skip


@dataclass(frozen=True, slots=True)
class RoleSelect:
  custom_id: str
  placeholder: str | None = None
  min_values: int | None = None
  max_values: int | None = None
  disabled: bool = False
  required: bool | None = None
  defaults: Sequence[int | str | Default] = ()
  id: int | None = None

  def to_dict(self) -> Json:
    return _select(
      6, self.custom_id, self.placeholder, self.min_values, self.max_values,
      self.disabled, self.required, self.id,
      default_values=_defaults("role", self.defaults) or None,
    )  # fmt: skip


@dataclass(frozen=True, slots=True)
class MentionableSelect:
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
    return _select(
      7, self.custom_id, self.placeholder, self.min_values, self.max_values,
      self.disabled, self.required, self.id,
      default_values=_defaults(None, self.defaults) or None,
    )  # fmt: skip


@dataclass(frozen=True, slots=True)
class ChannelSelect:
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
class ActionRow:
  """Up to five buttons, or one select."""

  components: Sequence[Component]
  id: int | None = None

  def __init__(self, *components: Component, id: int | None = None) -> None:
    object.__setattr__(self, "components", tuple(components))
    object.__setattr__(self, "id", id)

  def to_dict(self) -> Json:
    return _put(
      {"type": 1, "components": [c.to_dict() for c in self.components]}, id=self.id
    )


# Layout components (v2) ---------------------------------------------------------


@dataclass(frozen=True, slots=True)
class TextDisplay:
  """Markdown text. Counts toward the message's 4000 characters of text in total."""

  content: str
  id: int | None = None

  def to_dict(self) -> Json:
    return _put({"type": 10, "content": self.content}, id=self.id)


@dataclass(frozen=True, slots=True)
class Thumbnail:
  """A small image beside text: only as a `Section` accessory."""

  url: str
  description: str | None = None
  spoiler: bool = False
  id: int | None = None

  def to_dict(self) -> Json:
    value: Json = {"type": 11, "media": {"url": self.url}, "spoiler": self.spoiler}
    return _put(value, id=self.id, description=self.description)


@dataclass(frozen=True, slots=True)
class Section:
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
    texts = [t if isinstance(t, TextDisplay) else TextDisplay(t) for t in self.texts]
    value: Json = {
      "type": 9,
      "components": [t.to_dict() for t in texts],
      "accessory": self.accessory.to_dict(),
    }
    return _put(value, id=self.id)


@dataclass(frozen=True, slots=True)
class MediaItem:
  """One picture or video of a `MediaGallery`: a URL or `attachment://name`."""

  url: str
  description: str | None = None
  spoiler: bool = False

  def to_dict(self) -> Json:
    value: Json = {"media": {"url": self.url}, "spoiler": self.spoiler}
    return _put(value, description=self.description)


@dataclass(frozen=True, slots=True)
class MediaGallery:
  """Up to ten pictures or videos."""

  items: Sequence[MediaItem | str]
  id: int | None = None

  def __init__(self, *items: MediaItem | str, id: int | None = None) -> None:
    object.__setattr__(self, "items", tuple(items))
    object.__setattr__(self, "id", id)

  def to_dict(self) -> Json:
    items = [i if isinstance(i, MediaItem) else MediaItem(i) for i in self.items]
    return _put({"type": 12, "items": [i.to_dict() for i in items]}, id=self.id)


@dataclass(frozen=True, slots=True)
class File:
  """An uploaded file shown in the message; `url` is `attachment://name`."""

  url: str
  spoiler: bool = False
  id: int | None = None

  def __post_init__(self) -> None:
    if not self.url.startswith("attachment://"):
      raise ValueError("A File component shows an attachment: use attachment://name.")

  def to_dict(self) -> Json:
    value: Json = {"type": 13, "file": {"url": self.url}, "spoiler": self.spoiler}
    return _put(value, id=self.id)


@dataclass(frozen=True, slots=True)
class Separator:
  """Space between components, with an optional dividing line."""

  divider: bool = True
  spacing: Literal["small", "large"] = "small"
  id: int | None = None

  def to_dict(self) -> Json:
    value: Json = {
      "type": 14,
      "divider": self.divider,
      "spacing": 1 if self.spacing == "small" else 2,
    }
    return _put(value, id=self.id)


@dataclass(frozen=True, slots=True)
class Container:
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


def rows(components: Sequence[Any]) -> list[Json]:
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


def is_v2(components: Sequence[Any] | None) -> bool:
  """Whether a message's components use the layout set (so it is a v2 message)."""
  return any(
    isinstance(item, _LAYOUT)
    or (isinstance(item, Mapping) and item.get("type") in (9, 10, 11, 12, 13, 14, 17))
    for item in components or ()
  )


# Modal components ---------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class TextInput:
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
class GroupOption:
  """An option of a `RadioGroup` or `CheckboxGroup`."""

  label: str
  value: str
  description: str | None = None
  default: bool = False

  def to_dict(self) -> Json:
    value: Json = {"label": self.label, "value": self.value, "default": self.default}
    return _put(value, description=self.description)


def _group(options: Sequence[GroupOption | str]) -> list[Json]:
  return [
    (o if isinstance(o, GroupOption) else GroupOption(o, o)).to_dict() for o in options
  ]


@dataclass(frozen=True, slots=True)
class RadioGroup:
  """Pick exactly one of two to ten options."""

  custom_id: str
  options: Sequence[GroupOption | str]
  required: bool | None = None
  id: int | None = None

  def to_dict(self) -> Json:
    value: Json = {
      "type": 21,
      "custom_id": self.custom_id,
      "options": _group(self.options),
    }
    return _put(value, id=self.id, required=self.required)


@dataclass(frozen=True, slots=True)
class CheckboxGroup:
  """Pick any of up to ten options (`min_values`, `max_values` limit how many)."""

  custom_id: str
  options: Sequence[GroupOption | str]
  min_values: int | None = None
  max_values: int | None = None
  required: bool | None = None
  id: int | None = None

  def to_dict(self) -> Json:
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
class Checkbox:
  """A single yes/no box."""

  custom_id: str
  default: bool | None = None
  id: int | None = None

  def to_dict(self) -> Json:
    return _put(
      {"type": 23, "custom_id": self.custom_id}, id=self.id, default=self.default
    )


@dataclass(frozen=True, slots=True)
class FileUpload:
  """Ask for files; read them with `ctx.attachments` after the submission."""

  custom_id: str
  min_values: int | None = None
  max_values: int | None = None
  required: bool | None = None
  file_types: Sequence[str] = ()
  id: int | None = None

  def to_dict(self) -> Json:
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
class Label:
  """A titled field of a modal: wraps one input and gives it a label and a hint."""

  label: str
  component: ModalInput
  description: str | None = None
  id: int | None = None

  def to_dict(self) -> Json:
    value: Json = {
      "type": 18,
      "label": self.label,
      "component": self.component.to_dict(),
    }
    return _put(value, id=self.id, description=self.description)


@dataclass(frozen=True, slots=True)
class Modal:
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
    return self.components

  def to_dict(self) -> Json:
    built: list[Json] = []
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
    body["components"] = rows(components)
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
