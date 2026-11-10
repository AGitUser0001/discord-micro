"""What one Gateway connection knows about Discord: its guilds, held in memory.

A guild lives on exactly one shard, `(guild_id >> 22) % shard_count`, so the connection
serving that shard is the only place its roles, channels and members have to be kept. It
folds every dispatch it receives into a `ShardState`, and answers questions about it
(`GatewayWorker` serves them on `subjects.state(shard_id)`; `DiscordState` asks). Nothing
is stored: a connection that starts, or reconnects from scratch, is handed every guild
again by Discord (`GUILD_CREATE`).

Users belong to no guild, so each shard keeps the ones it has seen, stamped with when it
last heard of them; a question about a user goes to every shard and the newest answer
wins. A member is separate from its user: it is kept by guild (`<guild>:<user>`) and
linked to its user by id when it is read.
"""

import time
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import cast

from pydantic import JsonValue


@dataclass(frozen=True, slots=True)
class ProjectedObject:
  """One object to write to (or delete from) the aggregated state."""

  kind: str
  id: str
  guild_id: str | None
  payload: dict[str, JsonValue]
  deleted: bool = False


_STATE_KINDS = frozenset(
  (
    "guild",
    "user",
    "user_patch",
    "channel",
    "thread",
    "role",
    "member",
    "emoji",
    "voice_state",
    "presence",
    "stage_instance",
    "sticker",
    "scheduled_event",
  )
)
"""What is aggregated: the state of a guild. Messages, typing, reactions and the like are
events, not state, and are not kept."""


GUILD_MEMBERS_INTENT = 1 << 1
"""The intent that makes Discord send the member list (and member leaves and updates)."""

_MEMBER_KINDS = frozenset(("member", "presence"))


@dataclass(slots=True)
class _Guild:
  """One guild as a connection holds it."""

  objects: dict[str, dict[str, dict[str, JsonValue]]] = field(default_factory=dict)
  """Each kind's objects by id (`roles`, `channels`, `members` ... as `role`, ...)."""
  available: bool = True
  """False during a Discord outage of the guild: what is held is kept, but not served."""
  expecting: set[str] | None = None
  """The members delivered so far while the member list is on its way (else None)."""


class ShardState:
  """The guilds one connection holds, and the answers it gives about them."""

  def __init__(self) -> None:
    self._guilds: dict[str, _Guild] = {}
    self._users: dict[str, tuple[int, dict[str, JsonValue]]] = {}

  def clear(self) -> None:
    """Forget everything (a connection that starts over is handed it all again)."""
    self._guilds.clear()
    self._users.clear()

  # Folding dispatches in ----------------------------------------------------------

  def apply(self, name: str, payload: dict[str, JsonValue], *, chunks: bool) -> None:
    """Fold one dispatch in. `chunks` is whether the member list follows each
    `GUILD_CREATE` (the members intent): members it does not list are kept until the
    list is complete, then removed."""
    if name == "GUILD_DELETE":
      guild_id = _string_id(payload.get("id"))
      if guild_id is None:
        return
      if payload.get("unavailable") is True:
        if guild_id in self._guilds:
          self._guilds[guild_id].available = False  # an outage, not a removal
      else:
        self._guilds.pop(guild_id, None)
      return
    if name == "GUILD_CREATE":
      guild_id = _string_id(payload.get("id"))
      if guild_id is not None:
        old = self._guilds.get(guild_id)
        fresh = _Guild()
        if chunks:
          fresh.expecting = set()
          if old is not None:  # the list is coming and removes whoever is gone
            for kind in _MEMBER_KINDS:
              fresh.objects[kind] = dict(old.objects.get(kind, {}))
        self._guilds[guild_id] = fresh
    for item in _project_dispatch(name, payload):
      self._apply(item)
    if name == "GUILD_MEMBERS_CHUNK" and _finishes_member_list(payload):
      guild = self._guilds.get(_string_id(payload.get("guild_id")) or "")
      if guild is not None and guild.expecting is not None:
        for kind in _MEMBER_KINDS:
          held = guild.objects.get(kind, {})
          for object_id in [i for i in held if i not in guild.expecting]:
            del held[object_id]
        guild.expecting = None

  def _apply(self, item: ProjectedObject) -> None:
    if item.guild_id is None:
      if item.kind == "user" or item.kind == "user_patch" and item.id in self._users:
        self._users[item.id] = (time.time_ns(), self._merged(item.id, item.payload))
      return  # anything else not about a guild (a DM): there is nowhere to keep it
    guild = self._guilds.get(item.guild_id)
    if guild is None:
      return  # its state has not arrived: `GUILD_CREATE` brings it
    held = guild.objects.setdefault(item.kind, {})
    if item.deleted:
      held.pop(item.id, None)
      if item.kind == "member" and guild.expecting is not None:
        guild.expecting.discard(item.id)
      return
    held[item.id] = _merge_json(held.get(item.id, {}), item.payload)
    if item.kind == "member" and guild.expecting is not None:
      guild.expecting.add(item.id)

  def _merged(self, user_id: str, update: dict[str, JsonValue]) -> dict[str, JsonValue]:
    known = self._users.get(user_id)
    return _merge_json(known[1], update) if known is not None else dict(update)

  # Answering ----------------------------------------------------------------------

  def answer(self, operation: str, arguments: Mapping[str, JsonValue]) -> JsonValue:
    """The answer to one question, or None when this connection does not know."""
    guild_id = str(arguments.get("guild_id") or "")
    match operation:
      case "guild":
        return self._one(guild_id, "guild", guild_id)
      case "roles" | "channels":
        return self._all(guild_id, operation.removesuffix("s"))
      case "member":
        return self._member(guild_id, str(arguments.get("user_id")))
      case "role" | "channel":
        return self._where(operation, str(arguments.get("id")))
      case "user":
        found = self._users.get(str(arguments.get("user_id")))
        return None if found is None else {"stamp": found[0], "payload": found[1]}
      case "guilds_of":
        return self._guilds_of(str(arguments.get("user_id")))
    return None

  def _served(self, guild_id: str) -> _Guild | None:
    guild = self._guilds.get(guild_id)
    return guild if guild is not None and guild.available else None

  def _one(self, guild_id: str, kind: str, object_id: str) -> JsonValue:
    guild = self._served(guild_id)
    return None if guild is None else guild.objects.get(kind, {}).get(object_id)

  def _all(self, guild_id: str, kind: str) -> JsonValue:
    guild = self._served(guild_id)
    if guild is None:
      return None
    return list(guild.objects.get(kind, {}).values())

  def _member(self, guild_id: str, user_id: str) -> JsonValue:
    payload = self._one(guild_id, "member", f"{guild_id}:{user_id}")
    if not isinstance(payload, dict):
      return None
    user = self._users.get(user_id)
    return payload if user is None else {**payload, "user": user[1]}

  def _where(self, kind: str, object_id: str) -> JsonValue:
    """An object with a globally unique id (a channel, a role): its guild and payload."""
    for guild_id, guild in self._guilds.items():
      if guild.available and (payload := guild.objects.get(kind, {}).get(object_id)):
        return {"guild_id": guild_id, "payload": payload}
    return None

  def _guilds_of(self, user_id: str) -> JsonValue:
    """The guilds (themselves, not just ids) this shard knows the user to be in."""
    return cast(
      JsonValue,
      [
        guild.objects["guild"][guild_id]
        for guild_id, guild in self._guilds.items()
        if guild.available
        and guild_id in guild.objects.get("guild", {})
        and f"{guild_id}:{user_id}" in guild.objects.get("member", {})
      ],
    )


def _finishes_member_list(payload: dict[str, JsonValue]) -> bool:
  """Whether this is the last piece of a member list Micro asked for."""
  count = payload.get("chunk_count")
  return (
    isinstance(count, int)
    and payload.get("chunk_index") == count - 1
    and str(payload.get("nonce") or "").startswith("micro:")
  )


def _project_dispatch(
  name: str, payload: dict[str, JsonValue]
) -> tuple[ProjectedObject, ...]:
  deleted = name.endswith("_DELETE") or name in {
    "GUILD_DELETE",
    "THREAD_DELETE",
    "GUILD_MEMBER_REMOVE",
  }
  guild_id = _string_id(payload.get("guild_id"))
  if guild_id is None and name in {"GUILD_CREATE", "GUILD_UPDATE"}:
    guild_id = _string_id(payload.get("id"))
  objects: list[ProjectedObject] = []

  def add(kind: str, value: JsonValue, *, is_deleted: bool = False) -> None:
    if not isinstance(value, dict) or kind not in _STATE_KINDS:
      return
    object_guild = _string_id(value.get("guild_id")) or guild_id
    object_id = _object_id(kind, value, object_guild)
    if object_id is None:
      return
    if kind == "member" and isinstance(value.get("user"), dict):
      # A member and a user are separate: the user is the same in every guild, so it is
      # kept once on its own, and the member (keyed "<guild>:<user>") links back by id.
      value = {key: item for key, item in value.items() if key != "user"}
    objects.append(ProjectedObject(kind, object_id, object_guild, value, is_deleted))

  collections = {
    "guilds": "guild",
    "channels": "channel",
    "threads": "thread",
    "roles": "role",
    "members": "member",
    "emojis": "emoji",
    "voice_states": "voice_state",
    "presences": "presence",
    "stage_instances": "stage_instance",
    "stickers": "sticker",
    "guild_scheduled_events": "scheduled_event",
  }
  root_kind = _dispatch_kind(name)
  root = payload.get("role") if root_kind == "role" and "role" in payload else payload
  if name == "GUILD_ROLE_DELETE":
    root = {"id": payload.get("role_id"), "guild_id": payload.get("guild_id")}
  if root_kind == "guild" and isinstance(root, dict):
    # The lists are objects of their own, kept current one by one; left in the guild
    # they would only go stale.
    root = {key: value for key, value in root.items() if key not in collections}
  add(root_kind, root, is_deleted=deleted)
  presence_user = payload.get("user") if name == "PRESENCE_UPDATE" else None
  if isinstance(presence_user, dict) and isinstance(presence_user.get("id"), str):
    # A presence update carries only the user fields that changed: patch what is held.
    objects.append(
      ProjectedObject("user_patch", str(presence_user["id"]), None, presence_user)
    )
  for user in _users_in(payload):
    if user is not presence_user:
      objects.append(ProjectedObject("user", str(user["id"]), None, user))
  for collection, kind in collections.items():
    values = payload.get(collection)
    if isinstance(values, list):
      for value in values:
        add(kind, value)
  return tuple({(item.kind, item.id): item for item in objects}.values())


_USER_KEYS = frozenset(("user", "author", "inviter", "target_user", "creator"))
"""Keys under which Discord puts a whole user, wherever it appears: a member's `user`, a
message's `author` and `mentions`, a ban's `user`, an invite's `inviter`, a scheduled
event's `creator`, an interaction's resolved `users`, ..."""


def _users_in(payload: JsonValue) -> list[dict[str, JsonValue]]:
  """Every user a dispatch carries, found wherever it sits in the payload.

  A user changes through many events (a member joining or updating, a message, a
  reaction, typing, a voice change, a ban, an invite, a presence update, `USER_UPDATE`,
  the member list), all carrying the user, so all of them keep it current.
  """
  found: list[dict[str, JsonValue]] = []

  def is_user(value: JsonValue) -> bool:
    return (
      isinstance(value, dict)
      and isinstance(value.get("id"), str)
      and "username" in value  # a user (a role, a channel or a bare id has none)
    )

  def walk(
    value: JsonValue, key: str | None = None, parent: dict[str, JsonValue] | None = None
  ) -> None:
    if isinstance(value, dict):
      if key == "users":  # an interaction's resolved users, by id
        found.extend(
          item for item in value.values() if is_user(item) and isinstance(item, dict)
        )
      webhook = key == "author" and parent is not None and "webhook_id" in parent
      if key in _USER_KEYS and is_user(value) and not webhook:  # a webhook is no user
        found.append(value)
      for inner_key, inner in value.items():
        walk(inner, inner_key, value)
    elif isinstance(value, list):
      for inner in value:
        if key == "mentions" and is_user(inner):
          found.append(cast(dict[str, JsonValue], inner))
        walk(inner, key, parent)

  walk(payload)
  return found


def _dispatch_kind(name: str) -> str:
  if name.startswith("GUILD_MEMBER"):
    return "member"
  if name.startswith("GUILD_ROLE"):
    return "role"
  if name.startswith("GUILD_SCHEDULED_EVENT"):
    return "scheduled_event"
  if name.startswith("GUILD_EMOJIS"):
    return "guild"
  return (
    name.removesuffix("_CREATE").removesuffix("_UPDATE").removesuffix("_DELETE").lower()
  )


def _object_id(
  kind: str, value: Mapping[str, JsonValue], guild_id: str | None = None
) -> str | None:
  if kind in {"member", "presence"} and isinstance(value.get("user"), dict):
    # A user is a different member in every guild, so the id carries the guild.
    user = cast(dict[str, JsonValue], value["user"])
    user_id = _string_id(user.get("id"))
    return f"{guild_id}:{user_id}" if guild_id and user_id else user_id
  if kind == "voice_state":
    user_id = _string_id(value.get("user_id"))
    guild_id = _string_id(value.get("guild_id"))
    return f"{guild_id}:{user_id}" if guild_id and user_id else user_id
  return _string_id(value.get("id"))


def _string_id(value: JsonValue | None) -> str | None:
  return value if isinstance(value, str) and value else None


def _merge_json(
  current: dict[str, JsonValue], update: dict[str, JsonValue]
) -> dict[str, JsonValue]:
  merged = dict(current)
  for key, value in update.items():
    previous = merged.get(key)
    merged[key] = (
      _merge_json(previous, value)
      if isinstance(previous, dict) and isinstance(value, dict)
      else value
    )
  return merged


__all__ = ("GUILD_MEMBERS_INTENT", "ShardState")
