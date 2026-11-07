"""The interaction a handler receives, and every way to answer it.

Two layers, as in hikari. The low-level calls (`create_initial_response`,
`create_followup`, `edit_initial_response`, `delete_initial_response`) are one
Discord request each, named in Discord's vocabulary; they record what they sent
but never decide or refuse. The high-level calls (`respond`, `defer`,
`edit_response`, `delete_response`, `update_message`, `modal`, `autocomplete`)
read the interaction's state, pick the right low-level call, and raise a clear
error for a sequence Discord would reject.
"""

import asyncio
import json
import time
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from enum import IntEnum, StrEnum
from functools import cached_property
from typing import TYPE_CHECKING, Any

from pydantic import JsonValue

from micro.discord.objects import Attachment, Channel, Member, Message, Role, User
from micro.discord.routes import (
  APPLICATION_COMMAND,
  AUTOCOMPLETE,
  MESSAGE_COMPONENT,
  MODAL_SUBMIT,
)
from micro.discord.ui import (
  EPHEMERAL,
  ActionRow,
  AllowedMentions,
  Component,
  Json,
  Modal,
  message_body,
)
from micro.errors import MicroError

if TYPE_CHECKING:
  from micro.discord import DiscordHTTPClient
  from micro.discord.api import DiscordAPI
  from micro.discord.refs import ChannelRef, GuildRef, MemberRef, MessageRef, UserRef

TOKEN_LIFETIME = 15 * 60
_DISCORD_EPOCH_MS = 1420070400000
"""Discord interaction tokens stay valid for 15 minutes."""


class ResponseType(IntEnum):
  """Discord's interaction callback types."""

  MESSAGE_CREATE = 4
  DEFERRED_MESSAGE_CREATE = 5
  DEFERRED_MESSAGE_UPDATE = 6
  MESSAGE_UPDATE = 7
  AUTOCOMPLETE = 8
  MODAL = 9


type InputValue = str | bool | list[str] | None
"""What one modal field holds; see `Interaction.inputs`."""

CHECKBOX = 23
_MULTI = frozenset({3, 5, 6, 7, 8, 19, 22})
"""Component types that submit a list: selects, file upload, checkbox group."""


def _submitted(components: Sequence[Any] | None) -> Iterator[Mapping[str, Any]]:
  """Every field of a modal submission, through rows, labels and containers."""
  for item in components or ():
    if not isinstance(item, Mapping):
      continue
    if "custom_id" in item:
      yield item
    if isinstance(item.get("component"), Mapping):
      yield from _submitted([item["component"]])
    yield from _submitted(item.get("components"))


@dataclass(frozen=True)
class Resolved:
  """Discord's lookup table for the ids in an interaction, as typed objects."""

  users: dict[str, User] = field(default_factory=dict)
  members: dict[str, Member] = field(default_factory=dict)
  roles: dict[str, Role] = field(default_factory=dict)
  channels: dict[str, Channel] = field(default_factory=dict)
  attachments: dict[str, Attachment] = field(default_factory=dict)
  messages: dict[str, Message] = field(default_factory=dict)

  @classmethod
  def parse(cls, data: Mapping[str, Any] | None) -> Resolved:
    """Build a `Resolved` from Discord's `resolved` object (None gives an empty one)."""
    data = data or {}
    raw_users = data.get("users") or {}
    users = {k: User.model_validate(v) for k, v in raw_users.items()}
    members = {
      k: Member.model_validate({**v, "user": v.get("user") or raw_users.get(k)})
      for k, v in (data.get("members") or {}).items()
    }
    return cls(
      users=users,
      members=members,
      roles={k: Role.model_validate(v) for k, v in (data.get("roles") or {}).items()},
      channels={
        k: Channel.model_validate(v) for k, v in (data.get("channels") or {}).items()
      },
      attachments={
        k: Attachment.model_validate(v)
        for k, v in (data.get("attachments") or {}).items()
      },
      messages={
        k: Message.model_validate(v) for k, v in (data.get("messages") or {}).items()
      },
    )


REPLY_KEY = "micro_reply"
"""Set by `InteractionEndpoint` on an interaction it is holding open: the NATS subject
on which the first response is the HTTP response Discord is waiting for."""


async def respond_initially(
  http: DiscordHTTPClient, payload: Mapping[str, Any], body: Json
) -> None:
  """Send an interaction's first response.

  Interactions from the Gateway are answered with Discord's callback endpoint.
  One that arrived over HTTP (see `InteractionEndpoint`) is answered in the
  reply to that very request, which the endpoint is holding open.
  """
  reply = payload.get(REPLY_KEY)
  if isinstance(reply, str):
    await http.runtime.nats.publish(reply, json.dumps(body).encode())
    return
  await http.call(
    "create_interaction_response",
    path={"interaction_id": payload["id"], "interaction_token": payload["token"]},
    body=body,
  )


class InteractionState(StrEnum):
  """What has been sent for an interaction so far."""

  NEW = "not answered yet"
  DEFERRED_MESSAGE = "deferred in message mode"
  DEFERRED_UPDATE = "deferred in update mode"
  MESSAGE = "answered with a new message"
  UPDATED = "answered by updating its message"
  AUTOCOMPLETE = "answered with autocomplete choices"
  MODAL = "answered with a modal"


_AFTER = {
  ResponseType.MESSAGE_CREATE: InteractionState.MESSAGE,
  ResponseType.DEFERRED_MESSAGE_CREATE: InteractionState.DEFERRED_MESSAGE,
  ResponseType.DEFERRED_MESSAGE_UPDATE: InteractionState.DEFERRED_UPDATE,
  ResponseType.MESSAGE_UPDATE: InteractionState.UPDATED,
  ResponseType.AUTOCOMPLETE: InteractionState.AUTOCOMPLETE,
  ResponseType.MODAL: InteractionState.MODAL,
}


class InteractionExpired(MicroError, RuntimeError):
  """The interaction's 15-minute token expired; it can no longer be answered."""


class AlreadyResponded(MicroError, RuntimeError):
  """The interaction already has its one initial response."""


class InvalidResponse(MicroError, RuntimeError):
  """This response does not fit the interaction's type or state."""


class Interaction:
  """One routed interaction plus its response API.

  `respond` answers it: the first call is the initial response, a call after a
  message-mode `defer(thinking=True)` fills in the deferred message, and later
  calls are follow-ups. `defer()` acknowledges silently for components (update
  mode) and shows "thinking..." for commands. `update_message` edits the message
  a component sits on, and fails if the interaction was deferred in message
  mode, because the pending message is then a new one.
  """

  def __init__(
    self,
    payload: Mapping[str, Any],
    http: DiscordHTTPClient,
    *,
    received: float | None = None,
  ) -> None:
    self.payload = payload
    self.http = http
    self.received = time.monotonic() if received is None else received
    self.created_at: float = ((int(payload["id"]) >> 22) + _DISCORD_EPOCH_MS) / 1000
    """When Discord created the interaction (from its ID), as a Unix time."""
    self.route: Mapping[str, Any] = {}
    """What the matched `Route` extracted from the custom ID (`components.match`)."""
    self.id: str = payload["id"]
    self.token: str = payload["token"]
    self.application_id: str = payload["application_id"]
    self.type: int = payload["type"]
    self.data: Mapping[str, Any] = payload.get("data") or {}
    self.guild_id: str | None = payload.get("guild_id")
    self.channel_id: str | None = payload.get("channel_id") or (
      (payload.get("channel") or {}).get("id")
    )
    self.locale: str | None = payload.get("locale")
    member = payload.get("member")
    self.member: Member | None = Member.model_validate(member) if member else None
    user = payload.get("user") or (member or {}).get("user")
    self.user: User = User.model_validate(user or {"id": "0"})
    message = payload.get("message")
    self.message: Message | None = Message.model_validate(message) if message else None
    self.state = InteractionState.NEW
    self._lock = asyncio.Lock()

  # Introspection ---------------------------------------------------------------

  @property
  def custom_id(self) -> str | None:
    """The custom id of the component or modal, or None for a command."""
    return self.data.get("custom_id")

  @property
  def command_name(self) -> str | None:
    """The invoked command's name (the top-level one for subcommands)."""
    return self.data.get("name") if self.is_command or self.is_autocomplete else None

  @property
  def option_values(self) -> dict[str, str | int | float | bool]:
    """A command's submitted options by name (subcommand options included).

    Raw values: ids stay strings, see `resolved` for the entities they name.
    """
    values: dict[str, str | int | float | bool] = {}

    def collect(options: Any) -> None:
      for item in options or ():
        if "value" in item:
          values[item["name"]] = item["value"]
        else:
          collect(item.get("options"))

    collect(self.data.get("options"))
    return values

  # The rest of Discord, from here ----------------------------------------------------

  @property
  def api(self) -> DiscordAPI:
    """Every Discord operation as a method (`await ctx.api.create_message(...)`)."""
    return self.http.api

  @property
  def channel_ref(self) -> ChannelRef:
    """This interaction's channel, to send to, pin in, start a thread from, ..."""
    if self.channel_id is None:
      raise ValueError("This interaction has no channel.")
    return self.api.channel(self.channel_id)

  @property
  def guild_ref(self) -> GuildRef:
    """This interaction's server: ban, roles, channels, emojis, events, ..."""
    if self.guild_id is None:
      raise ValueError("This interaction did not happen in a server.")
    return self.api.guild(self.guild_id)

  @property
  def user_ref(self) -> UserRef:
    """The user who triggered this, to direct-message and so on."""
    return self.api.user(self.user.id)

  @property
  def member_ref(self) -> MemberRef:
    """The triggering user as a member of this server: kick, timeout, roles, ..."""
    if self.guild_id is None:
      raise ValueError("This interaction did not happen in a server.")
    return self.api.member(self.guild_id, self.user.id)

  @property
  def message_ref(self) -> MessageRef:
    """The message a component is on (edit it, pin it, react, start a thread, ...)."""
    if self.message is None or self.channel_id is None:
      raise ValueError("This interaction did not come from a message.")
    return self.api.message(self.channel_id, self.message.id)

  @property
  def values(self) -> list[str]:
    """Selected values of a select menu interaction."""
    return list(self.data.get("values") or [])

  @property
  def inputs(self) -> dict[str, InputValue]:
    """Everything a modal submission holds, by custom_id.

    Text inputs and radio groups give a string (None: nothing chosen), selects,
    checkbox groups and file uploads a list of strings (ids, for the entity selects
    and uploads: see `users`, `roles`, `channels`, `attachments`), a checkbox a bool.
    """
    found: dict[str, InputValue] = {}
    for component in _submitted(self.data.get("components")):
      key = component["custom_id"]
      kind = component.get("type")
      if kind in _MULTI:
        found[key] = [str(item) for item in component.get("values") or []]
      elif kind == CHECKBOX:
        found[key] = bool(component.get("value"))
      else:
        found[key] = component.get("value")
    return found

  @property
  def fields(self) -> dict[str, str]:
    """The text inputs and radio groups of a modal submission, as strings."""
    return {
      key: value or ""
      for key, value in self.inputs.items()
      if not isinstance(value, bool | list)
    }

  def choices(self, custom_id: str | None = None) -> list[str]:
    """What a select, checkbox group or upload picked: raw values, or ids.

    Without a `custom_id`, the select a button-like interaction came from.
    """
    if custom_id is None:
      return self.values
    value = self.inputs.get(custom_id)
    return list(value) if isinstance(value, list) else []

  @cached_property
  def resolved(self) -> Resolved:
    """The users, members, roles, channels, attachments and messages the
    interaction's selected values or options refer to."""
    return Resolved.parse(self.data.get("resolved"))

  def users(self, custom_id: str | None = None) -> list[User]:
    """The users picked in a user or mentionable select."""
    return [
      self.resolved.users[i]
      for i in self.choices(custom_id)
      if i in self.resolved.users
    ]

  def members(self, custom_id: str | None = None) -> list[Member]:
    """The picked users as guild members, where Discord resolved them."""
    return [
      self.resolved.members[i]
      for i in self.choices(custom_id)
      if i in self.resolved.members
    ]

  def roles(self, custom_id: str | None = None) -> list[Role]:
    """The roles picked in a role or mentionable select."""
    return [
      self.resolved.roles[i]
      for i in self.choices(custom_id)
      if i in self.resolved.roles
    ]

  def channels(self, custom_id: str | None = None) -> list[Channel]:
    """The channels picked in a channel select."""
    return [
      self.resolved.channels[i]
      for i in self.choices(custom_id)
      if i in self.resolved.channels
    ]

  def attachments(self, custom_id: str | None = None) -> list[Attachment]:
    """The files uploaded to a file upload field."""
    found = self.resolved.attachments
    return [found[i] for i in self.choices(custom_id) if i in found]

  @property
  def age(self) -> float:
    """Seconds since Discord created the interaction (needs a sane clock)."""
    return max(0.0, time.time() - self.created_at)

  @property
  def expired(self) -> bool:
    """Whether the interaction token (valid 15 minutes) has expired."""
    return time.monotonic() - self.received >= TOKEN_LIFETIME

  @property
  def responded(self) -> bool:
    """Whether an initial response has been sent."""
    return self.state is not InteractionState.NEW

  @property
  def deferred(self) -> bool:
    """Whether the interaction was deferred and not yet answered."""
    return self.state in (
      InteractionState.DEFERRED_MESSAGE,
      InteractionState.DEFERRED_UPDATE,
    )

  @property
  def is_command(self) -> bool:
    """True for slash, user and message commands."""
    return self.type == APPLICATION_COMMAND

  @property
  def is_component(self) -> bool:
    """True for button clicks and select choices."""
    return self.type == MESSAGE_COMPONENT

  @property
  def is_modal(self) -> bool:
    """True for modal submissions."""
    return self.type == MODAL_SUBMIT

  @property
  def is_autocomplete(self) -> bool:
    """True for autocomplete requests."""
    return self.type == AUTOCOMPLETE

  # Low level: one Discord request each -----------------------------------------

  async def create_initial_response(
    self, kind: ResponseType, data: Json | None = None
  ) -> None:
    """Create Interaction Response: the one callback an interaction gets."""
    async with self._lock:
      await self._initial(kind, data)

  async def create_followup(self, body: Json) -> Message:
    """Create Followup Message (a new message after the initial response)."""
    async with self._lock:
      return await self._followup(body)

  async def edit_initial_response(self, body: Json) -> None:
    """Edit Original Interaction Response (the @original webhook message)."""
    async with self._lock:
      await self._edit(body)

  async def delete_initial_response(self) -> None:
    """Delete Original Interaction Response."""
    async with self._lock:
      await self._delete()

  # High level: state-aware -----------------------------------------------------

  async def respond(
    self,
    content: str | None = None,
    *,
    embeds: Sequence[Json] = (),
    components: Sequence[ActionRow | Component] | None = None,
    ephemeral: bool = False,
    allowed_mentions: AllowedMentions | None = None,
  ) -> Message | None:
    """Answer the interaction with a message.

    The initial response when nothing was sent, the deferred message after a
    `defer(thinking=True)`, and a follow-up (returned) otherwise.
    """
    body = message_body(
      content,
      embeds=embeds,
      components=components,
      allowed_mentions=allowed_mentions,
      ephemeral=ephemeral,
    )
    async with self._lock:
      match self.state:
        case InteractionState.NEW:
          await self._initial(ResponseType.MESSAGE_CREATE, body)
          return None
        case InteractionState.DEFERRED_MESSAGE:
          body.pop("flags", None)
          await self._edit(body)
          return None
        case InteractionState.MODAL | InteractionState.AUTOCOMPLETE:
          raise AlreadyResponded(f"The interaction is {self.state.value}.")
        case _:
          return await self._followup(body)

  async def defer(self, *, thinking: bool = False, ephemeral: bool = False) -> None:
    """Acknowledge now and answer later.

    On a component (or a modal opened from one) this is silent update mode, so
    `update_message` and `respond` both work afterwards; `thinking=True` shows
    "thinking..." and the next `respond` fills it in. Commands always think.
    `ephemeral` applies to thinking deferrals only, because an update keeps the
    visibility of the message it edits.
    """
    if self.is_autocomplete:
      raise InvalidResponse("Autocomplete interactions cannot be deferred.")
    async with self._lock:
      self._require(InteractionState.NEW, "defer")
      if (self.is_component or self.is_modal) and self.message and not thinking:
        await self._initial(ResponseType.DEFERRED_MESSAGE_UPDATE)
      else:
        data: Json | None = {"flags": EPHEMERAL} if ephemeral else None
        await self._initial(ResponseType.DEFERRED_MESSAGE_CREATE, data)

  async def edit_response(
    self,
    content: str | None = None,
    *,
    embeds: Sequence[Json] | None = None,
    components: Sequence[ActionRow | Component] | None = None,
    allowed_mentions: AllowedMentions | None = None,
  ) -> None:
    """Edit the message this interaction answered with."""
    body = _edit_body(content, embeds, components, allowed_mentions)
    async with self._lock:
      self._require_original("edit")
      await self._edit(body)

  async def delete_response(self) -> None:
    """Delete the message this interaction answered with."""
    async with self._lock:
      self._require_original("delete")
      await self._delete()

  async def update_message(
    self,
    content: str | None = None,
    *,
    embeds: Sequence[Json] | None = None,
    components: Sequence[ActionRow | Component] | None = None,
    allowed_mentions: AllowedMentions | None = None,
  ) -> None:
    """Edit the message a component was clicked on.

    Needs a source message: always there for components, and for modal submits
    only when the modal was opened from one. Fails after a message-mode defer
    or a new-message response, where the original is no longer that message.
    """
    if not (self.is_component or self.is_modal) or self.message is None:
      raise InvalidResponse(
        "update_message() needs the message a component was clicked on, and this "
        "interaction has none; use respond() or edit_response()."
      )
    body = _edit_body(content, embeds, components, allowed_mentions)
    async with self._lock:
      match self.state:
        case InteractionState.NEW:
          await self._initial(ResponseType.MESSAGE_UPDATE, body)
        case InteractionState.DEFERRED_UPDATE | InteractionState.UPDATED:
          await self._edit(body)
        case InteractionState.DEFERRED_MESSAGE:
          raise InvalidResponse(
            "update_message() after defer(thinking=True): the pending message is "
            "a new one. Use respond(), or defer() without thinking."
          )
        case _:
          raise InvalidResponse(
            f"update_message() but the interaction is {self.state.value}; "
            "use edit_response() to change what it sent."
          )

  async def modal(self, modal: Modal) -> None:
    """Show a modal; it must be the initial response."""
    if self.is_modal or self.is_autocomplete:
      raise InvalidResponse("A modal cannot answer a modal submit or an autocomplete.")
    async with self._lock:
      self._require(InteractionState.NEW, "show a modal", AlreadyResponded)
      await self._initial(ResponseType.MODAL, modal.to_dict())

  async def autocomplete(self, choices: Sequence[Any]) -> None:
    """Send autocomplete suggestions (at most 25, Discord's limit)."""
    from ._commands import Choice

    if not self.is_autocomplete:
      raise InvalidResponse("Suggestions only answer autocomplete interactions.")
    if len(choices) > 25:
      raise ValueError("Discord accepts at most 25 autocomplete choices.")
    items: list[JsonValue] = [
      (choice if isinstance(choice, Choice) else Choice(str(choice), choice)).to_dict()
      for choice in choices
    ]
    async with self._lock:
      self._require(InteractionState.NEW, "send suggestions", AlreadyResponded)
      await self._initial(ResponseType.AUTOCOMPLETE, {"choices": items})

  # Plumbing (callers hold the lock) --------------------------------------------

  def _check(self) -> None:
    if self.expired:
      raise InteractionExpired(
        f"Interaction {self.id} is older than 15 minutes and can no longer be answered."
      )

  def _require(
    self,
    state: InteractionState,
    action: str,
    error: type[MicroError] = AlreadyResponded,
  ) -> None:
    if self.state is not state:
      raise error(f"Cannot {action}: the interaction is {self.state.value}.")

  def _require_original(self, action: str) -> None:
    if self.state in (
      InteractionState.NEW,
      InteractionState.MODAL,
      InteractionState.AUTOCOMPLETE,
    ):
      raise InvalidResponse(
        f"Cannot {action} the response: the interaction is {self.state.value}."
      )

  async def _initial(self, kind: ResponseType, data: Json | None = None) -> None:
    self._check()
    body: Json = {"type": int(kind)}
    if data is not None:
      body["data"] = data
    await respond_initially(self.http, self.payload, body)
    self.state = _AFTER[kind]

  async def _followup(self, body: Json) -> Message:
    self._check()
    result = await self.http.call(
      "execute_webhook",
      path={"webhook_id": self.application_id, "webhook_token": self.token},
      query={"wait": True},
      body=body,
    )
    return Message.model_validate(result)

  async def _edit(self, body: Json) -> None:
    self._check()
    await self.http.call(
      "update_original_webhook_message",
      path={"webhook_id": self.application_id, "webhook_token": self.token},
      body=body,
    )
    if self.state is InteractionState.DEFERRED_MESSAGE:
      self.state = InteractionState.MESSAGE
    elif self.state is InteractionState.DEFERRED_UPDATE:
      self.state = InteractionState.UPDATED

  async def _delete(self) -> None:
    self._check()
    await self.http.call(
      "delete_original_webhook_message",
      path={"webhook_id": self.application_id, "webhook_token": self.token},
    )


def _edit_body(
  content: str | None,
  embeds: Sequence[Json] | None,
  components: Sequence[ActionRow | Component] | None,
  allowed_mentions: AllowedMentions | None,
) -> Json:
  body = message_body(
    content,
    embeds=embeds or (),
    components=components,
    allowed_mentions=allowed_mentions,
  )
  if embeds is not None and not embeds:
    body["embeds"] = []
  return body
