"""Small builders for message content: embeds, components, modals, mentions."""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from typing import Any, Literal

type Json = dict[str, Any]

EPHEMERAL = 1 << 6
_BUTTON_STYLES = {"primary": 1, "secondary": 2, "success": 3, "danger": 4, "link": 5}


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
  image: str | None = None,
  thumbnail: str | None = None,
  author: str | None = None,
) -> Json:
  """Build an embed; `fields` are `(name, value)` or `(name, value, inline)`."""
  value: Json = {}
  for key, item in (
    ("title", title),
    ("description", description),
    ("color", color),
    ("url", url),
  ):
    if item is not None:
      value[key] = item
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
    value["footer"] = {"text": footer}
  if image is not None:
    value["image"] = {"url": image}
  if thumbnail is not None:
    value["thumbnail"] = {"url": thumbnail}
  if author is not None:
    value["author"] = {"name": author}
  return value


@dataclass(frozen=True, slots=True)
class Button:
  label: str | None = None
  custom_id: str | None = None
  url: str | None = None
  style: Literal["primary", "secondary", "success", "danger", "link"] = "primary"
  emoji: str | None = None
  disabled: bool = False

  def __post_init__(self) -> None:
    if (self.url is None) == (self.custom_id is None):
      raise ValueError("A button needs exactly one of custom_id or url.")

  def to_dict(self) -> Json:
    value: Json = {
      "type": 2,
      "style": _BUTTON_STYLES["link" if self.url else self.style],
      "disabled": self.disabled,
    }
    if self.label is not None:
      value["label"] = self.label
    if self.url is not None:
      value["url"] = self.url
    else:
      value["custom_id"] = self.custom_id
    if self.emoji is not None:
      value["emoji"] = {"name": self.emoji}
    return value


@dataclass(frozen=True, slots=True)
class SelectOption:
  label: str
  value: str
  description: str | None = None
  default: bool = False

  def to_dict(self) -> Json:
    value: Json = {"label": self.label, "value": self.value, "default": self.default}
    if self.description is not None:
      value["description"] = self.description
    return value


@dataclass(frozen=True, slots=True)
class Select:
  """A string select menu; options may be strings or `SelectOption`s."""

  custom_id: str
  options: Sequence[SelectOption | str]
  placeholder: str | None = None
  min_values: int = 1
  max_values: int = 1
  disabled: bool = False

  def to_dict(self) -> Json:
    value: Json = {
      "type": 3,
      "custom_id": self.custom_id,
      "options": [
        (
          option if isinstance(option, SelectOption) else SelectOption(option, option)
        ).to_dict()
        for option in self.options
      ],
      "min_values": self.min_values,
      "max_values": self.max_values,
      "disabled": self.disabled,
    }
    if self.placeholder is not None:
      value["placeholder"] = self.placeholder
    return value


type Component = Button | Select


@dataclass(frozen=True, slots=True)
class ActionRow:
  components: Sequence[Component]

  def __init__(self, *components: Component) -> None:
    object.__setattr__(self, "components", tuple(components))

  def to_dict(self) -> Json:
    return {
      "type": 1,
      "components": [component.to_dict() for component in self.components],
    }


def rows(components: Sequence[ActionRow | Component]) -> list[Json]:
  """Lay out components: rows stay; loose buttons fill rows of five; selects get a row."""
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
    laid_out.append(
      item.to_dict() if isinstance(item, ActionRow) else ActionRow(item).to_dict()
    )
  flush()
  return laid_out


@dataclass(frozen=True, slots=True)
class TextInput:
  custom_id: str
  label: str
  style: Literal["short", "paragraph"] = "short"
  required: bool = True
  placeholder: str | None = None
  value: str | None = None
  min_length: int | None = None
  max_length: int | None = None

  def to_dict(self) -> Json:
    data: Json = {
      "type": 4,
      "custom_id": self.custom_id,
      "label": self.label,
      "style": 1 if self.style == "short" else 2,
      "required": self.required,
    }
    for key in ("placeholder", "value", "min_length", "max_length"):
      if (item := getattr(self, key)) is not None:
        data[key] = item
    return data


@dataclass(frozen=True, slots=True)
class Modal:
  custom_id: str
  title: str
  inputs: Sequence[TextInput] = field(default_factory=tuple)

  def to_dict(self) -> Json:
    return {
      "custom_id": self.custom_id,
      "title": self.title,
      "components": [
        {"type": 1, "components": [item.to_dict()]} for item in self.inputs
      ],
    }


def message_body(
  content: str | None = None,
  *,
  embeds: Sequence[Json] = (),
  components: Sequence[ActionRow | Component] | None = None,
  allowed_mentions: AllowedMentions | None = None,
  ephemeral: bool = False,
) -> Json:
  """A message payload with safe mention defaults."""
  body: Json = {
    "allowed_mentions": (allowed_mentions or AllowedMentions.none()).to_dict()
  }
  if content is not None:
    body["content"] = content
  if embeds:
    body["embeds"] = list(embeds)
  if components is not None:
    body["components"] = rows(components)
  if ephemeral:
    body["flags"] = EPHEMERAL
  return body
