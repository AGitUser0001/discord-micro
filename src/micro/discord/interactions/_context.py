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
import time
from collections.abc import Mapping, Sequence
from enum import IntEnum, StrEnum
from typing import TYPE_CHECKING, Any

from micro.discord.objects import Member, Message, User
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
    return self.data.get("custom_id")

  @property
  def values(self) -> list[str]:
    """Selected values of a select menu interaction."""
    return list(self.data.get("values") or [])

  @property
  def fields(self) -> dict[str, str]:
    """Text input values of a modal submission, by custom_id."""
    values: dict[str, str] = {}
    for row in self.data.get("components") or []:
      for component in row.get("components") or [row.get("component") or {}]:
        if "custom_id" in component:
          values[component["custom_id"]] = component.get("value", "")
    return values

  @property
  def age(self) -> float:
    """Seconds since Discord created the interaction (needs a sane clock)."""
    return max(0.0, time.time() - self.created_at)

  @property
  def expired(self) -> bool:
    return time.monotonic() - self.received >= TOKEN_LIFETIME

  @property
  def responded(self) -> bool:
    return self.state is not InteractionState.NEW

  @property
  def deferred(self) -> bool:
    return self.state in (
      InteractionState.DEFERRED_MESSAGE,
      InteractionState.DEFERRED_UPDATE,
    )

  @property
  def is_command(self) -> bool:
    return self.type == APPLICATION_COMMAND

  @property
  def is_component(self) -> bool:
    return self.type == MESSAGE_COMPONENT

  @property
  def is_modal(self) -> bool:
    return self.type == MODAL_SUBMIT

  @property
  def is_autocomplete(self) -> bool:
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
        data = {"flags": EPHEMERAL} if ephemeral else None
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
    items = [
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
    await self.http.call(
      "create_interaction_response",
      path={"interaction_id": self.id, "interaction_token": self.token},
      body=body,
    )
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
