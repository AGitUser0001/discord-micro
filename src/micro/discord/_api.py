"""The runtime under `micro.discord.api`: turn keyword arguments into one request.

`api.py` (generated, one method per Discord operation) calls `_call`. It drops
what you did not pass, accepts Micro's builders where Discord wants JSON (components,
allowed mentions, embeds), checks the result against Discord's own request model so
a mistake is a `ValidationError` before anything is sent, and returns the typed
success body, or raises `DiscordAPIError`.
"""

from collections.abc import Mapping, Sequence
from datetime import datetime
from enum import Enum
from types import UnionType
from typing import (
  TYPE_CHECKING,
  Annotated,
  Any,
  TypeAliasType,
  Union,
  get_args,
  get_origin,
)

from pydantic import BaseModel
from pydantic_core import from_json

from micro.discord import ui
from micro.discord.http_operations import HTTP_OPERATIONS, DiscordOperationId
from micro.discord.http_service import (
  DiscordAPIError,
  DiscordHTTPFile,
  DiscordHTTPResponse,
)
from micro.discord.ui import Upload
from micro.result import Err, Ok

if TYPE_CHECKING:
  from micro.discord.http_service import DiscordHTTPClient
  from micro.discord.refs import (
    ChannelRef,
    CommandRef,
    EmojiRef,
    GuildRef,
    InviteRef,
    MemberRef,
    MessageRef,
    RoleRef,
    ScheduledEventRef,
    StickerRef,
    UserRef,
    WebhookRef,
    WebhookTokenRef,
  )


class _Unset:
  def __repr__(self) -> str:
    return "UNSET"

  def __bool__(self) -> bool:
    return False


UNSET: Any = _Unset()
"""The default of every optional argument: not passed, as opposed to None (a value)."""


def _plain(value: Any) -> Any:
  """JSON-able: builders, models and enums become what Discord reads."""
  if isinstance(value, Enum):
    return value.value
  if isinstance(value, BaseModel):
    return value.model_dump(mode="json", by_alias=True, exclude_none=True)
  if hasattr(value, "to_dict"):
    return value.to_dict()
  if isinstance(value, datetime):
    return value.isoformat()
  if isinstance(value, Mapping):
    return {key: _plain(item) for key, item in value.items() if item is not UNSET}
  if isinstance(value, bytes):
    return value
  if isinstance(value, Sequence) and not isinstance(value, str):
    return [_plain(item) for item in value]
  return value


def _wants_text(annotation: Any) -> bool:
  """Whether a field is a string or a snowflake (a string-valued RootModel)."""
  if annotation is str:
    return True
  return (
    isinstance(annotation, type)
    and issubclass(annotation, BaseModel)
    and "root" in annotation.model_fields
    and annotation.model_fields["root"].annotation is str
  )


def _fit(value: Any, annotation: Any) -> Any:
  """Make plain Python values fit a model: ids given as ints become strings.

  Discord ids are strings in its models, so `create_message(123, ...)` works because
  this walks the value alongside the annotation and converts, at any depth. It
  never raises; anything it cannot place is left for the model to judge.
  """
  if isinstance(annotation, TypeAliasType):
    annotation = annotation.__value__
  origin, args = get_origin(annotation), get_args(annotation)
  if origin is Annotated:
    return _fit(value, args[0])
  if origin in (Union, UnionType):
    members = [a for a in args if a is not type(None)]
    if isinstance(value, int) and not isinstance(value, bool):
      if any(_wants_text(a) for a in members) and not any(a is int for a in members):
        return str(value)
      return value
    if isinstance(value, Mapping):
      keys = set(value)
      scored = [
        (len(keys & _field_names(a)), a)
        for a in members
        if isinstance(a, type) and issubclass(a, BaseModel)
      ]
      if scored:
        return _fit(value, max(scored, key=lambda pair: pair[0])[1])
    if isinstance(value, Sequence) and not isinstance(value, str | bytes):
      inner = _list_member(members)
      return [_fit(item, inner) for item in value]
    return value
  if isinstance(value, bool):
    return value
  if isinstance(value, int) and _wants_text(annotation):
    return str(value)
  if (
    origin in (list, set, frozenset, tuple)
    and isinstance(value, Sequence)
    and not isinstance(value, str | bytes)
  ):
    return [_fit(item, args[0] if args else Any) for item in value]
  if origin is dict and isinstance(value, Mapping) and len(args) > 1:
    return {key: _fit(item, args[1]) for key, item in value.items()}
  if isinstance(annotation, type) and issubclass(annotation, BaseModel):
    if "root" in annotation.model_fields and len(annotation.model_fields) == 1:
      return _fit(value, annotation.model_fields["root"].annotation)
    if isinstance(value, Mapping):
      by_wire = {(i.alias or n): i for n, i in annotation.model_fields.items()}
      by_name = dict(annotation.model_fields)
      return {
        key: _fit(item, (by_wire.get(key) or by_name.get(key)).annotation)  # pyright: ignore[reportOptionalMemberAccess]
        if key in by_wire or key in by_name
        else item
        for key, item in value.items()
      }
  return value


def _field_names(model: Any) -> set[str]:
  return {i.alias or n for n, i in model.model_fields.items()} | set(model.model_fields)


def _list_member(members: list[Any]) -> Any:
  """The element type of a `X | list[Y]` union, for a list value."""
  for member in members:
    if get_origin(member) in (list, set, frozenset, tuple) and get_args(member):
      return get_args(member)[0]
  return Any


def _body_fields(annotation: Any) -> dict[str, Any]:
  """The field names a request body can have, through `X | None` and unions of models."""
  found: dict[str, Any] = {}
  stack = [annotation]
  while stack:
    item = stack.pop()
    if isinstance(item, type) and issubclass(item, BaseModel):
      if "root" in item.model_fields and len(item.model_fields) == 1:
        stack.append(item.model_fields["root"].annotation)
      else:
        found.update(item.model_fields)
    else:
      stack.extend(getattr(item, "__args__", ()))
  return found


def _message_rules(body: dict[str, Any], fields: Mapping[str, Any]) -> None:
  """What Micro does for every message: safe mentions, laid-out components, v2 flag."""
  components = body.get("components")
  if isinstance(components, Sequence) and not isinstance(components, str):
    if ui.is_v2(components):
      if body.get("content") or body.get("embeds"):
        raise ValueError(
          "A message with layout components (TextDisplay, Container, ...) has no "
          "content or embeds: put the text in a TextDisplay."
        )
      body["flags"] = int(body.get("flags") or 0) | ui.IS_COMPONENTS_V2
    laid_out = ui.rows(components)
    body["components"] = list(laid_out)
    ui.enforce(ui.message_measures(laid_out), "This message")
  has_text = body.get("content") or body.get("embeds") or body.get("components")
  if "allowed_mentions" in fields and "allowed_mentions" not in body and has_text:
    body["allowed_mentions"] = ui.AllowedMentions.none().to_dict()


def _shown(body: Mapping[str, Any]) -> tuple[Upload, ...]:
  """The uploads a message body's embeds and components show."""
  embeds, components = body.get("embeds"), body.get("components")
  return ui.uploads_in(
    embeds=embeds if isinstance(embeds, Sequence) else (),
    components=components
    if isinstance(components, Sequence) and not isinstance(components, str)
    else None,
  )


def _path_value(value: Any) -> Any:
  """A path argument: an Emoji is written `name` or `name:id`, as Discord reads it."""
  if isinstance(value, ui.Emoji):
    return f"{value.name}:{value.id}" if value.id is not None else value.name
  return _plain(value)


class ApiBase:
  """What the generated methods share, and the way to a ref."""

  def __init__(self, http: DiscordHTTPClient) -> None:
    self.http = http

  # Refs: an object by id, its ids bound (see refs.py) -------------------------------

  def channel(self, channel_id: int | str) -> ChannelRef:
    from micro.discord.refs import ChannelRef

    return ChannelRef(self, str(channel_id))  # type: ignore[arg-type]

  def message(self, channel_id: int | str, message_id: int | str) -> MessageRef:
    from micro.discord.refs import MessageRef

    return MessageRef(self, str(channel_id), str(message_id))  # type: ignore[arg-type]

  def guild(self, guild_id: int | str) -> GuildRef:
    from micro.discord.refs import GuildRef

    return GuildRef(self, str(guild_id))  # type: ignore[arg-type]

  def member(self, guild_id: int | str, user_id: int | str) -> MemberRef:
    from micro.discord.refs import MemberRef

    return MemberRef(self, str(guild_id), str(user_id))  # type: ignore[arg-type]

  def role(self, guild_id: int | str, role_id: int | str) -> RoleRef:
    from micro.discord.refs import RoleRef

    return RoleRef(self, str(guild_id), str(role_id))  # type: ignore[arg-type]

  def user(self, user_id: int | str) -> UserRef:
    from micro.discord.refs import UserRef

    return UserRef(self, str(user_id))  # type: ignore[arg-type]

  def emoji(self, guild_id: int | str, emoji_id: int | str) -> EmojiRef:
    from micro.discord.refs import EmojiRef

    return EmojiRef(self, str(guild_id), str(emoji_id))  # type: ignore[arg-type]

  def sticker(self, guild_id: int | str, sticker_id: int | str) -> StickerRef:
    from micro.discord.refs import StickerRef

    return StickerRef(self, str(guild_id), str(sticker_id))  # type: ignore[arg-type]

  def event(self, guild_id: int | str, event_id: int | str) -> ScheduledEventRef:
    from micro.discord.refs import ScheduledEventRef

    return ScheduledEventRef(self, str(guild_id), str(event_id))  # type: ignore[arg-type]

  def webhook(self, webhook_id: int | str) -> WebhookRef:
    from micro.discord.refs import WebhookRef

    return WebhookRef(self, str(webhook_id))  # type: ignore[arg-type]

  def webhook_token(self, webhook_id: int | str, token: str) -> WebhookTokenRef:
    from micro.discord.refs import WebhookTokenRef

    return WebhookTokenRef(self, str(webhook_id), token)  # type: ignore[arg-type]

  def invite(self, code: str) -> InviteRef:
    from micro.discord.refs import InviteRef

    return InviteRef(self, code)  # type: ignore[arg-type]

  def command(self, application_id: int | str, command_id: int | str) -> CommandRef:
    from micro.discord.refs import CommandRef

    return CommandRef(self, str(application_id), str(command_id))  # type: ignore[arg-type]

  async def _try(
    self,
    operation: DiscordOperationId,
    path: Mapping[str, Any],
    query: Mapping[str, Any],
    body: Any = UNSET,
    *,
    files: Sequence[Upload] | None = None,
    reason: str | None = None,
  ) -> Any:
    """`_call`, with Discord's refusal as an `Err` value; a mistake in the call itself
    (a bad argument, no worker running) still raises."""
    try:
      return Ok(
        await self._call(operation, path, query, body, files=files, reason=reason)
      )
    except DiscordAPIError as error:
      return Err(error)

  async def _call(
    self,
    operation: DiscordOperationId,
    path: Mapping[str, Any],
    query: Mapping[str, Any],
    body: Any = UNSET,
    *,
    files: Sequence[Upload] | None = None,
    reason: str | None = None,
  ) -> Any:
    definition = HTTP_OPERATIONS[operation]
    request_model = definition.request_model
    data: dict[str, Any] = {}
    if definition.path_fields:
      data["path"] = {k: _path_value(v) for k, v in path.items()}
    if query_values := {k: _plain(v) for k, v in query.items() if v is not UNSET}:
      data["query"] = query_values
    uploads: list[DiscordHTTPFile] = []
    if body is not UNSET:
      if isinstance(body, Mapping):
        known = _body_fields(request_model.model_fields["body"].annotation)
        payload = {k: v for k, v in body.items() if v is not UNSET}
        for name, value in list(payload.items()):
          if isinstance(value, Upload):  # a declared file field (stickers, ...)
            uploads.append(
              DiscordHTTPFile(
                field=name,
                filename=value.filename,
                data=value.data,
                content_type=value.content_type,
              )
            )
            payload[name] = (
              b""  # the model wants bytes; the real ones travel in `files`
            )
        draft = payload.get("content")
        if isinstance(draft, ui.Draft):
          payload.pop("content")
          clash = sorted(
            name
            for name in ("embeds", "components", "allowed_mentions", "tts")
            if name in payload
          )
          if clash or files:
            raise TypeError(
              "Pass a Draft, or content/embeds/components/files/..., not both "
              f"({', '.join(clash + (['files'] if files else []))} given with it)."
            )
          files = list(draft.uploads)
          payload.update(draft.to_dict())
        shown = _shown(payload)
        if shown or files:
          files = ui.uploads_in(files=[*(files or ()), *shown])
          if (
            definition.method.upper() == "POST"
            and "attachments" in known
            and "attachments" not in payload
            and any(file.description for file in files)
          ):
            payload["attachments"] = ui.attachments(files)
        _message_rules(payload, known)
        data["body"] = _plain(payload)
      else:
        data["body"] = _plain(body)
    for index, upload in enumerate(files or ()):
      uploads.append(
        DiscordHTTPFile(
          field=f"files[{index}]",
          filename=upload.name,
          data=upload.data,
          content_type=upload.content_type,
        )
      )
    request = request_model.model_validate(_fit(data, request_model))
    response = await self.http._request_operation(  # pyright: ignore[reportPrivateUsage]
      operation, request, uploads, reason
    )
    status: int = response.status  # pyright: ignore[reportAttributeAccessIssue]
    if status >= 400:
      raise DiscordAPIError(
        operation,
        DiscordHTTPResponse(
          status=status,
          headers=response.headers,  # pyright: ignore[reportAttributeAccessIssue]
          body=response.raw_body,  # pyright: ignore[reportAttributeAccessIssue]
        ),
      )
    result = response.body  # pyright: ignore[reportAttributeAccessIssue]
    raw: bytes = response.raw_body  # pyright: ignore[reportAttributeAccessIssue]
    if result is None and raw:
      return from_json(raw)  # a body the generated model does not describe: plain JSON
    while isinstance(result, BaseModel) and "root" in type(result).model_fields:
      result = result.root  # pyright: ignore[reportAttributeAccessIssue]
    return result
