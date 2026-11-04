"""The interaction a handler receives, and every way to answer it."""

import asyncio
import time
from collections.abc import Mapping, Sequence
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
"""Discord interaction tokens stay valid for 15 minutes."""

_PONG, _MESSAGE, _DEFER, _DEFER_UPDATE, _UPDATE, _AUTOCOMPLETE, _MODAL = (
  1,
  4,
  5,
  6,
  7,
  8,
  9,
)


class InteractionExpired(MicroError, RuntimeError):
  """The interaction's 15-minute token expired; it can no longer be answered."""


class AlreadyResponded(MicroError, RuntimeError):
  """The interaction already has its one initial response."""


class Interaction:
  """One routed interaction plus its response API.

  The first answer is the initial response (`reply`, `defer`, `update`, `modal`,
  `autocomplete`); later `reply` calls become follow-ups automatically, and a
  `reply` after a deferral fills in the deferred message.
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
    self.responded = False
    self.deferred = False
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
  def expired(self) -> bool:
    return time.monotonic() - self.received >= TOKEN_LIFETIME

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

  # Responses -------------------------------------------------------------------

  async def reply(
    self,
    content: str | None = None,
    *,
    embeds: Sequence[Json] = (),
    components: Sequence[ActionRow | Component] | None = None,
    ephemeral: bool = False,
    allowed_mentions: AllowedMentions | None = None,
  ) -> None:
    """Answer the interaction; follow up if it was already answered."""
    body = message_body(
      content,
      embeds=embeds,
      components=components,
      allowed_mentions=allowed_mentions,
      ephemeral=ephemeral,
    )
    async with self._lock:
      if not self.responded:
        await self._callback(_MESSAGE, body)
        return
      if self.deferred:
        self.deferred = False
        body.pop("flags", None)
        await self._edit_original(body)
        return
    await self.followup_body(body)

  async def followup(
    self,
    content: str | None = None,
    *,
    embeds: Sequence[Json] = (),
    components: Sequence[ActionRow | Component] | None = None,
    ephemeral: bool = False,
    allowed_mentions: AllowedMentions | None = None,
  ) -> Message:
    """Send another message after the initial response."""
    return await self.followup_body(
      message_body(
        content,
        embeds=embeds,
        components=components,
        allowed_mentions=allowed_mentions,
        ephemeral=ephemeral,
      )
    )

  async def followup_body(self, body: Json) -> Message:
    self._check()
    if not self.responded:
      raise RuntimeError("Respond to the interaction before following up.")
    result = await self.http.call(
      "execute_webhook",
      path={"webhook_id": self.application_id, "webhook_token": self.token},
      query={"wait": True},
      body=body,
    )
    return Message.model_validate(result)

  async def defer(self, *, ephemeral: bool = False) -> None:
    """Acknowledge now and answer later (shows "thinking..." for commands)."""
    async with self._lock:
      if self.responded:
        return
      if self.type == MESSAGE_COMPONENT:
        await self._callback(_DEFER_UPDATE, None)
      else:
        await self._callback(_DEFER, {"flags": EPHEMERAL} if ephemeral else None)
      self.deferred = True

  async def update(
    self,
    content: str | None = None,
    *,
    embeds: Sequence[Json] | None = None,
    components: Sequence[ActionRow | Component] | None = None,
    allowed_mentions: AllowedMentions | None = None,
  ) -> None:
    """Edit the message a component belongs to (or the original response)."""
    body = message_body(
      content,
      embeds=embeds or (),
      components=components,
      allowed_mentions=allowed_mentions,
    )
    if embeds is not None and not embeds:
      body["embeds"] = []
    async with self._lock:
      if not self.responded and self.type in (MESSAGE_COMPONENT, MODAL_SUBMIT):
        await self._callback(_UPDATE, body)
        return
    self.deferred = False
    await self._edit_original(body)

  async def edit(
    self,
    content: str | None = None,
    *,
    embeds: Sequence[Json] | None = None,
    components: Sequence[ActionRow | Component] | None = None,
    allowed_mentions: AllowedMentions | None = None,
  ) -> None:
    """Edit the original response."""
    body = message_body(
      content,
      embeds=embeds or (),
      components=components,
      allowed_mentions=allowed_mentions,
    )
    self.deferred = False
    await self._edit_original(body)

  async def delete(self) -> None:
    """Delete the original response."""
    self._check()
    await self.http.call(
      "delete_original_webhook_message",
      path={"webhook_id": self.application_id, "webhook_token": self.token},
    )

  async def modal(self, modal: Modal) -> None:
    """Show a modal; it must be the initial response."""
    async with self._lock:
      if self.responded:
        raise AlreadyResponded("A modal must be the initial response.")
      await self._callback(_MODAL, modal.to_dict())

  async def autocomplete(self, choices: Sequence[Any]) -> None:
    """Send autocomplete suggestions (at most 25, Discord's limit)."""
    from ._commands import Choice

    if len(choices) > 25:
      raise ValueError("Discord accepts at most 25 autocomplete choices.")
    items = [
      (choice if isinstance(choice, Choice) else Choice(str(choice), choice)).to_dict()
      for choice in choices
    ]
    async with self._lock:
      if self.responded:
        raise AlreadyResponded("Autocomplete suggestions were already sent.")
      await self._callback(_AUTOCOMPLETE, {"choices": items})

  # Plumbing --------------------------------------------------------------------

  def _check(self) -> None:
    if self.expired:
      raise InteractionExpired(
        f"Interaction {self.id} is older than 15 minutes and can no longer be answered."
      )

  async def _callback(self, kind: int, data: Json | None) -> None:
    self._check()
    if self.responded:
      raise AlreadyResponded("The interaction already has its initial response.")
    body: Json = {"type": kind}
    if data is not None:
      body["data"] = data
    await self.http.call(
      "create_interaction_response",
      path={"interaction_id": self.id, "interaction_token": self.token},
      body=body,
    )
    self.responded = True

  async def _edit_original(self, body: Json) -> None:
    self._check()
    await self.http.call(
      "update_original_webhook_message",
      path={"webhook_id": self.application_id, "webhook_token": self.token},
      body=body,
    )
