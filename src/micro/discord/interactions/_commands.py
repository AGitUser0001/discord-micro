"""Application commands declared from typed Python functions."""

import inspect
import re
import types
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass, field
from itertools import pairwise
from typing import (
  TYPE_CHECKING,
  Annotated,
  Any,
  Concatenate,
  Literal,
  Protocol,
  Union,
  get_args,
  get_origin,
  get_type_hints,
)

from pydantic import JsonValue

from micro.discord.enums import CommandType
from micro.discord.objects import Attachment, Channel, Member, Role, User

from ._inject import leading

if TYPE_CHECKING:
  from ._application import Context
  from ._context import Interaction

_NAME = re.compile(r"^[-_\w]{1,32}$")

type Handler[**P] = (
  Callable[Concatenate["Context", "Interaction", P], Awaitable[Any]]
  | Callable[Concatenate["Interaction", P], Awaitable[Any]]
  | Callable[Concatenate["Context", P], Awaitable[Any]]
)
"""A command, component or modal handler: it asks for the `Context`, the `Interaction`, or
both (in that order), and the rest is the command's own options (`P`)."""


class Registrar(Protocol):
  """What a command decorator returns: it takes a handler of any shape above and gives back
  the `Command` it registered."""

  def __call__[**P](self, handler: Handler[P], /) -> Command: ...


class Marker(Protocol):
  """What a decorator that only registers returns: the handler, unchanged."""

  def __call__[**P](self, handler: Handler[P], /) -> Handler[P]: ...


type ChoiceValue = str | int | float


class CommandOutdated(LookupError):
  """Discord's copy of a command is older than this handler (a rollout is converging)."""


@dataclass(frozen=True, slots=True)
class Choice:
  """A choice for an option or autocomplete: shown `name`, submitted `value`."""

  name: str
  value: ChoiceValue
  name_localizations: Mapping[str, str] | None = None

  def to_dict(self) -> dict[str, JsonValue]:
    """This component as the JSON object Discord expects."""
    value: dict[str, JsonValue] = {"name": self.name, "value": self.value}
    if self.name_localizations:
      value["name_localizations"] = dict(self.name_localizations)
    return value


@dataclass(frozen=True, slots=True)
class Option:
  """Describe a command option: `topic: Annotated[str, Option("What about")]`."""

  description: str = "-"
  name: str | None = None
  choices: Sequence[Choice | ChoiceValue] | None = None
  min_value: int | float | None = None
  max_value: int | float | None = None
  min_length: int | None = None
  max_length: int | None = None
  channel_types: Sequence[int] | None = None
  name_localizations: Mapping[str, str] | None = None
  description_localizations: Mapping[str, str] | None = None


class Mentionable:
  """Annotation for a user-or-role option; the value is a `User` or `Role`."""


_TYPES: dict[Any, int] = {
  str: 3,
  int: 4,
  bool: 5,
  User: 6,
  Member: 6,
  Channel: 7,
  Role: 8,
  Mentionable: 9,
  float: 10,
  Attachment: 11,
}


@dataclass(slots=True)
class OptionSpec:
  name: str
  parameter: str
  python_type: Any
  discord_type: int
  required: bool
  option: Option
  autocomplete: bool = False
  nullable: bool = False
  """Optional by its type (`X | None`) with no default: None when not given."""

  def to_dict(self) -> dict[str, JsonValue]:
    value: dict[str, JsonValue] = {
      "type": self.discord_type,
      "name": self.name,
      "description": self.option.description,
      "required": self.required,
    }
    option = self.option
    if option.choices:
      value["choices"] = [
        (
          choice if isinstance(choice, Choice) else Choice(str(choice), choice)
        ).to_dict()
        for choice in option.choices
      ]
    for key in ("min_value", "max_value", "min_length", "max_length"):
      if (item := getattr(option, key)) is not None:
        value[key] = item
    if option.channel_types:
      value["channel_types"] = list(option.channel_types)
    if option.name_localizations:
      value["name_localizations"] = dict(option.name_localizations)
    if option.description_localizations:
      value["description_localizations"] = dict(option.description_localizations)
    if self.autocomplete:
      value["autocomplete"] = True
    return value


def _validate_name(name: str, *, lower: bool = True) -> str:
  if not _NAME.match(name) or (lower and name != name.lower()):
    raise ValueError(f"{name!r} is not a valid Discord command or option name.")
  return name


def parse_options(handler: Handler) -> list[OptionSpec]:
  """Read slash-command options from a handler's parameters after the first."""
  hints = get_type_hints(handler, include_extras=True)
  parameters = list(inspect.signature(handler).parameters.values())[
    len(leading(handler)) :
  ]
  specs: list[OptionSpec] = []
  for parameter in parameters:
    annotation = hints.get(parameter.name, str)
    option = Option()
    if get_origin(annotation) is Annotated:
      annotation, *extras = get_args(annotation)
      option = next((item for item in extras if isinstance(item, Option)), option)
    required = parameter.default is inspect.Parameter.empty
    if get_origin(annotation) in (Union, types.UnionType):
      members = [arg for arg in get_args(annotation) if arg is not type(None)]
      if len(members) != len(get_args(annotation)):
        required = False
      annotation = members[0] if len(members) == 1 else Mentionable
    choices = option.choices
    if get_origin(annotation) is Literal:
      values = get_args(annotation)
      choices = choices or values
      annotation = type(values[0])
    if annotation not in _TYPES:
      raise TypeError(
        f"Unsupported command option type for {parameter.name!r}: {annotation!r}"
      )
    if choices is not option.choices:
      option = Option(**{**_option_fields(option), "choices": choices})
    specs.append(
      OptionSpec(
        _validate_name(option.name or parameter.name),
        parameter.name,
        annotation,
        _TYPES[annotation],
        required,
        option,
        nullable=not required and parameter.default is inspect.Parameter.empty,
      )
    )
  if any(not a.required and b.required for a, b in pairwise(specs)):
    raise ValueError("Required options must come before optional ones.")
  return specs


def _option_fields(option: Option) -> dict[str, JsonValue]:
  return {name: getattr(option, name) for name in Option.__dataclass_fields__}


@dataclass(slots=True)
class Command:
  """One slash, user, or message command (or a slash subcommand)."""

  name: str
  handler: Handler
  description: str = "-"
  type: CommandType = CommandType.CHAT
  options: list[OptionSpec] = field(default_factory=list)
  autocompleters: dict[str, Handler] = field(default_factory=dict)
  guild_ids: tuple[int, ...] = ()
  default_member_permissions: int | None = None
  contexts: tuple[int, ...] | None = None
  integration_types: tuple[int, ...] | None = None
  nsfw: bool = False
  name_localizations: Mapping[str, str] | None = None
  description_localizations: Mapping[str, str] | None = None

  def autocomplete(self, option: str) -> Marker:
    """Register suggestions for one string/number option."""

    def register(handler: Handler) -> Handler:
      spec = next((item for item in self.options if item.name == option), None)
      if spec is None:
        raise ValueError(f"Command {self.name!r} has no option {option!r}.")
      if spec.discord_type not in (3, 4, 10):
        raise ValueError(
          "Only string, integer, and number options support autocomplete."
        )
      spec.autocomplete = True
      self.autocompleters[option] = handler
      return handler

    return register

  def to_dict(self) -> dict[str, JsonValue]:
    """This command as Discord's application command JSON."""
    value: dict[str, JsonValue] = {
      "type": self.type,
      "name": self.name,
      "nsfw": self.nsfw,
    }
    if self.type == CommandType.CHAT:
      value["description"] = self.description
      value["options"] = [option.to_dict() for option in self.options]
    _common(value, self)
    return value

  def option_dict(self) -> dict[str, JsonValue]:
    """This command as a subcommand option."""
    value: dict[str, JsonValue] = {
      "type": 1,
      "name": self.name,
      "description": self.description,
      "options": [option.to_dict() for option in self.options],
    }
    if self.name_localizations:
      value["name_localizations"] = dict(self.name_localizations)
    return value


@dataclass(slots=True)
class CommandGroup:
  """A slash command with subcommands (and at most one level of groups)."""

  name: str
  description: str = "-"
  children: dict[str, Command | CommandGroup] = field(default_factory=dict)
  guild_ids: tuple[int, ...] = ()
  default_member_permissions: int | None = None
  contexts: tuple[int, ...] | None = None
  integration_types: tuple[int, ...] | None = None
  nsfw: bool = False
  name_localizations: Mapping[str, str] | None = None
  description_localizations: Mapping[str, str] | None = None
  nested: bool = False
  type: CommandType = CommandType.CHAT

  def command(self, name: str, *, description: str = "-") -> Registrar:
    """Decorator: add a subcommand to this group."""

    def register(handler: Handler) -> Command:
      _require_async(handler)
      command = Command(
        _validate_name(name),
        handler,
        description,
        options=parse_options(handler),
      )
      self._add(command)
      return command

    return register

  def group(self, name: str, *, description: str = "-") -> CommandGroup:
    """Add a nested subcommand group (Discord allows one level)."""
    if self.nested:
      raise ValueError("Discord allows only one level of subcommand groups.")
    group = CommandGroup(_validate_name(name), description, nested=True)
    self._add(group)
    return group

  def _add(self, child: Command | CommandGroup) -> None:
    if child.name in self.children:
      raise ValueError(f"{self.name!r} already has a subcommand {child.name!r}.")
    self.children[child.name] = child

  def option_dict(self) -> dict[str, JsonValue]:
    """This group as a subcommand-group option of its parent."""
    return {
      "type": 2,
      "name": self.name,
      "description": self.description,
      "options": [child.option_dict() for child in self.children.values()],
    }

  def to_dict(self) -> dict[str, JsonValue]:
    """This group as Discord's application command JSON."""
    value: dict[str, JsonValue] = {
      "type": CommandType.CHAT,
      "name": self.name,
      "description": self.description,
      "nsfw": self.nsfw,
      "options": [child.option_dict() for child in self.children.values()],
    }
    _common(value, self)
    return value

  def resolve(
    self, options: list[dict[str, Any]]
  ) -> tuple[Command, list[dict[str, Any]]]:
    """Find the subcommand a set of submitted options names."""
    for item in options:
      child = self.children.get(item.get("name", ""))
      if child is None:
        continue
      nested = item.get("options") or []
      if isinstance(child, CommandGroup):
        return child.resolve(nested)
      return child, nested
    raise LookupError(f"Unknown subcommand of {self.name!r}.")


def _common(value: dict[str, JsonValue], source: Command | CommandGroup) -> None:
  if source.default_member_permissions is not None:
    value["default_member_permissions"] = str(source.default_member_permissions)
  if source.contexts is not None:
    value["contexts"] = list(source.contexts)
  if source.integration_types is not None:
    value["integration_types"] = list(source.integration_types)
  if source.name_localizations:
    value["name_localizations"] = dict(source.name_localizations)
  if source.description_localizations:
    value["description_localizations"] = dict(source.description_localizations)


def _require_async(handler: Handler) -> None:
  if not inspect.iscoroutinefunction(handler):
    raise TypeError("Interaction handlers must be async functions.")


def convert_options(
  specs: Sequence[OptionSpec],
  values: Sequence[Mapping[str, Any]],
  resolved: Mapping[str, Any],
  guild_id: str | None = None,
  context: Any = None,
) -> dict[str, JsonValue]:
  """Turn interaction option values into handler keyword arguments (`guild_id`: the
  server the interaction happened in, which resolved members belong to).

  Options this handler does not declare are ignored and optional ones it does
  declare fall back to their defaults, so old and new versions both work while
  a rollout converges. A missing required option raises `CommandOutdated`.
  """
  given = {item.get("name"): item.get("value") for item in values}
  arguments: dict[str, JsonValue] = {}
  for spec in specs:
    if spec.name not in given:
      if spec.required:
        raise CommandOutdated(f"Discord did not send required option {spec.name!r}.")
      if spec.nullable:
        arguments[spec.parameter] = None
      continue
    raw = given[spec.name]
    arguments[spec.parameter] = _bind(_convert(spec, raw, resolved, guild_id), context)
  return arguments


def _bind(value: Any, context: Any) -> Any:
  """A resolved object bound to the context, so its actions work."""
  return (
    value.bind(context) if context is not None and hasattr(value, "bind") else value
  )


def _convert(
  spec: OptionSpec, raw: Any, resolved: Mapping[str, Any], guild_id: str | None
) -> Any:
  users = resolved.get("users") or {}
  members = resolved.get("members") or {}
  if spec.python_type is User:
    return User.model_validate(users[raw])
  if spec.python_type is Member:
    return Member.model_validate(
      {**members.get(raw, {}), "user": users.get(raw), "guild_id": guild_id}
    )
  if spec.python_type is Role:
    return Role.model_validate(
      {**(resolved.get("roles") or {})[raw], "guild_id": guild_id}
    )
  if spec.python_type is Channel:
    return Channel.model_validate((resolved.get("channels") or {})[raw])
  if spec.python_type is Attachment:
    return Attachment.model_validate((resolved.get("attachments") or {})[raw])
  if spec.python_type is Mentionable:
    if raw in users:
      return User.model_validate(users[raw])
    return Role.model_validate(
      {**(resolved.get("roles") or {})[raw], "guild_id": guild_id}
    )
  return spec.python_type(raw)


__all__ = (
  "Choice",
  "Command",
  "CommandGroup",
  "Mentionable",
  "Option",
)
