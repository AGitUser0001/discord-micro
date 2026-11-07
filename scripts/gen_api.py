"""Generate src/micro/discord/api.py: one flat method per Discord operation.

    uv run python scripts/gen_api.py

Path parameters are positional; query and body fields are keyword arguments (required
ones without a default, the rest defaulting to UNSET, "not passed"); an operation whose
body is a list or a union takes it as `body`. Operations that accept uploads take
`files=[Upload(...)]`, and every operation that changes something takes `reason=` for
the audit log. The success body comes back typed; failures raise DiscordAPIError.
"""

import types
import typing
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, IntEnum, StrEnum
from pathlib import Path
from typing import Any, Literal, TypeAliasType, Union, get_args, get_origin

from pydantic import AnyUrl, BaseModel, RootModel

import micro.discord.models.http as http_models
import micro.discord.models.http_requests as requests
from micro.discord.http_operations import HTTP_OPERATIONS

OUT = Path(__file__).resolve().parent.parent / "src/micro/discord/api.py"
REFS_OUT = OUT.with_name("refs.py")
RESERVED = {"self", "files", "reason", "body"}
ERRORS = {"RatelimitedResponse", "ErrorResponse"}


def exported(cls: type) -> bool:
  return getattr(http_models, cls.__name__, None) is cls


def render(ann: Any, *, strict: bool = False) -> str:
  """An annotation as source. Inputs are lenient (a dict for a model, a str for a
  datetime); `strict` renders what comes back."""
  if ann is Any or ann is None or ann is type(None):
    return "Any" if ann is Any else "None"
  if isinstance(ann, TypeAliasType):
    return render(ann.__value__, strict=strict)
  origin, args = get_origin(ann), get_args(ann)
  if origin is typing.Annotated:
    return render(args[0], strict=strict)
  if origin in (Union, types.UnionType):
    atoms = [atom for a in args for atom in render(a, strict=strict).split(" | ")]
    return " | ".join(dict.fromkeys(atoms))
  if origin is Literal:
    return "Literal[" + ", ".join(repr(a) for a in args) + "]"
  if origin in (list, set, frozenset, tuple, Sequence):
    inner = render(args[0], strict=strict) if args else "Any"
    return f"list[{inner}]" if strict else f"Sequence[{inner}]"
  if origin in (dict, Mapping):
    value = render(args[1], strict=strict) if len(args) > 1 else "Any"
    return f"dict[str, {value}]" if strict else f"Mapping[str, {value}]"
  if isinstance(ann, type):
    if ann is bytes:
      return "bytes"
    if ann in (str, int, float, bool):
      return ann.__name__
    if ann is datetime or ann.__name__ == "AwareDatetime":
      return "datetime" if strict else "datetime | str"
    if ann is AnyUrl:
      return "str"
    if ann.__name__ == "SnowflakeType":
      return "str" if strict else "int | str"
    if issubclass(ann, Enum):
      name = f"m.{ann.__name__}" if exported(ann) else "Any"
      if strict:
        return name
      return f"{name} | {'int' if issubclass(ann, IntEnum) else 'str' if issubclass(ann, StrEnum) else 'Any'}"
    if issubclass(ann, RootModel):
      if strict and exported(ann):
        return f"m.{ann.__name__}"
      return render(ann.model_fields["root"].annotation, strict=strict)
    if issubclass(ann, BaseModel):
      if not exported(ann):
        return "Mapping[str, Any]" if not strict else "Any"
      return f"m.{ann.__name__}" if strict else f"m.{ann.__name__} | Mapping[str, Any]"
  return "Any"


def render_body(ann: Any) -> str:
  """A top-level success body, as the API returns it: wrappers (RootModel) opened."""
  while (
    isinstance(ann, type)
    and issubclass(ann, RootModel)
    and ann.__name__ != "SnowflakeType"
  ):
    ann = unwrap(ann.model_fields["root"].annotation)
  return render(ann, strict=True)


def success_type(op: Any) -> str:
  if op.success_statuses == (204,) or not op.success_statuses:
    return "None"
  root = op.response_body_model.model_fields["root"].annotation
  members = [
    a for a in (get_args(root) or (root,)) if getattr(a, "__name__", "") not in ERRORS
  ]
  if not members:
    return "None"
  rendered = dict.fromkeys(render_body(a) for a in members)
  return " | ".join(rendered)


def unwrap(ann: Any) -> Any:
  """`X | None` is X."""
  members = [a for a in get_args(ann) if a is not type(None)]
  if get_origin(ann) in (Union, types.UnionType) and len(members) == 1:
    return members[0]
  return ann


def fields_of(model: Any) -> list[tuple[str, str, Any]]:
  """(python name, wire name, FieldInfo) for a request part's model."""
  model = unwrap(model)
  if model is None or not (isinstance(model, type) and issubclass(model, BaseModel)):
    return []
  return [(name, info.alias or name, info) for name, info in model.model_fields.items()]


def union_models(ann: Any) -> list[type[BaseModel]] | None:
  """The models of a body that is a union of models, else None."""
  ann = unwrap(ann)
  if not (isinstance(ann, type) and issubclass(ann, RootModel)):
    return None
  members = [
    a for a in get_args(ann.model_fields["root"].annotation) if a is not type(None)
  ]
  plain = [
    a for a in members
    if isinstance(a, type) and issubclass(a, BaseModel) and not issubclass(a, RootModel)
  ]  # fmt: skip
  return plain if plain and len(plain) == len(members) else None


def merged_fields(models: list[type[BaseModel]]) -> list[tuple[str, str, Any]]:
  """Fields across a union's members, each once and optional (the right member is picked
  when the request is checked)."""
  merged: dict[str, tuple[str, str, Any]] = {}
  for model in models:
    for name, wire, info in fields_of(model):
      merged.setdefault(name, (name, wire, info))
  return list(merged.values())


@dataclass
class Shape:
  """One operation as arguments: what the flat method and a ref method share."""

  op: Any
  path: list[tuple[str, str, str]]  # (argument, wire name, annotation)
  required: list[tuple[str, str]]
  optional: list[tuple[str, str]]
  lead: list[
    tuple[str, str]
  ]  # `content`: optional, but given positionally like send("hi")
  query_items: list[str]
  body_items: list[str]
  root_body: str | None  # the annotation of a list or union `body`, else None
  has_body: bool
  takes_files: bool
  returns: str

  @property
  def keyword_names(self) -> list[str]:
    return [n for n, _ in self.required + self.optional + self.lead]


def shape(op: Any) -> Shape:
  req = getattr(requests, op.request)
  parts = req.model_fields
  path = fields_of(parts["path"].annotation) if "path" in parts else []
  query = fields_of(parts["query"].annotation) if "query" in parts else []
  body_ann = unwrap(parts["body"].annotation) if "body" in parts else None
  union = union_models(body_ann)
  root_body = (
    isinstance(body_ann, type) and issubclass(body_ann, RootModel) and union is None
  )
  body = merged_fields(union) if union else ([] if root_body else fields_of(body_ann))
  multipart = "multipart/form-data" in op.content_types
  taken: set[str] = set()

  def name_of(raw: str) -> str:
    name = raw + "_" if raw in RESERVED else raw
    assert name not in taken, f"{op.id}: {name} appears twice"
    taken.add(name)
    return name

  path_args: list[tuple[str, str, str]] = []
  for n, wire, i in path:
    ann = "str | Emoji" if n == "emoji_name" else render(i.annotation)
    path_args.append((name_of(n), wire, ann))
  required: list[tuple[str, str]] = []
  optional: list[tuple[str, str]] = []
  lead: list[tuple[str, str]] = []
  query_items: list[str] = []
  body_items: list[str] = []
  has_upload_slot = False
  for source, collected in ((query, query_items), (body, body_items)):
    for raw, wire, info in source:
      if wire.startswith("files["):
        has_upload_slot = True
        continue
      name = name_of(raw)
      is_file = "bytes" in str(info.annotation)
      ann = "Upload" if is_file else render(info.annotation)
      if wire == "components" and "Sequence" in ann:
        # Micro's builders (Button, Container, ...) as well as Discord's own models.
        ann = (
          "Sequence[Buildable | Mapping[str, Any]] | None"
          if "None" in ann
          else "Sequence[Buildable | Mapping[str, Any]]"
        )
      if wire == "allowed_mentions":
        ann = "AllowedMentions | " + ann
      if raw == "content" and (not info.is_required() or union):
        lead.append((name, ann))
      else:
        (required if info.is_required() and not union else optional).append((name, ann))
      collected.append(f'"{wire}": {name}')
  takes_files = (
    multipart and "application/json" in op.content_types
  ) or has_upload_slot
  return Shape(
    op=op,
    path=path_args,
    required=required,
    optional=optional,
    lead=lead,
    query_items=query_items,
    body_items=body_items,
    root_body=render(body_ann) if root_body else None,
    has_body="body" in parts,
    takes_files=takes_files,
    returns=success_type(op),
  )


def extras_of(sh: Shape) -> list[str]:
  extras: list[str] = []
  if sh.takes_files:
    extras.append("files: Sequence[Upload] | None = None")
  if sh.op.method != "GET":
    extras.append("reason: str | None = None")
  return extras


def method(op: Any) -> str:
  sh = shape(op)
  positional = [f"{n}: {ann}" for n, _, ann in sh.path]
  if sh.root_body is not None:
    positional.append(f"body: {sh.root_body}")
  positional += [f"{n}: {a} = UNSET" for n, a in sh.lead]
  extras = extras_of(sh)
  keywords = [f"{n}: {a}" for n, a in sh.required] + [
    f"{n}: {a} = UNSET" for n, a in sh.optional
  ]
  star = ["*"] if (keywords or extras) else []
  signature = ",\n    ".join(["self", *positional, *star, *keywords, *extras])
  path_map = ", ".join(f'"{wire}": {n}' for n, wire, _ in sh.path)
  call = [f'"{op.id}"', "{" + path_map + "}", "{" + ", ".join(sh.query_items) + "}"]
  if sh.root_body is not None:
    call.append("body")
  elif sh.has_body:
    call.append("{" + ", ".join(sh.body_items) + "}")
  if sh.takes_files:
    call.append("files=files")
  if op.method != "GET":
    call.append("reason=reason")
  return (
    f"  async def {op.id}(\n    {signature},\n  ) -> {sh.returns}:\n"
    f'    """{op.method} {op.path}"""\n'
    f"    return await self._call({', '.join(call)})\n"
  )


# Refs: ids bound once, the rest as arguments ----------------------------------------


@dataclass
class RefSpec:
  ids: tuple[str, ...]
  doc: str
  methods: dict[str, str | tuple[str, dict[str, str]]]
  """Method name to an operation id, or (operation id, {argument: python expression}).
  An operation's path ids that the ref has are bound; an argument given an expression
  is fixed to it and left out of the signature."""
  links: dict[str, tuple[str, tuple[str, ...]]] = field(default_factory=dict)
  """Method name to (another ref, the new ids it takes): the ref's own ids carry over."""
  mixin: str | None = None


REFS: dict[str, RefSpec] = {
  "ChannelRef": RefSpec(
    ("channel_id",),
    "A channel, thread or DM by id.",
    {
      "get": "get_channel",
      "edit": "update_channel",
      "delete": "delete_channel",
      "send": "create_message",
      "history": "list_messages",
      "typing": "trigger_typing_indicator",
      "pins": "list_pins",
      "pin": "create_pin",
      "unpin": "delete_pin",
      "bulk_delete": "bulk_delete_messages",
      "invites": "list_channel_invites",
      "create_invite": "create_channel_invite",
      "webhooks": "list_channel_webhooks",
      "create_webhook": "create_webhook",
      "follow": "follow_channel",
      "start_thread": "create_thread",
      "join": "join_thread",
      "leave": "leave_thread",
      "thread_members": "list_thread_members",
      "thread_member": "get_thread_member",
      "add_thread_member": "add_thread_member",
      "remove_thread_member": "delete_thread_member",
      "public_archived_threads": "list_public_archived_threads",
      "private_archived_threads": "list_private_archived_threads",
      "my_private_archived_threads": "list_my_private_archived_threads",
      "search_threads": "thread_search",
      "set_permissions": "set_channel_permission_overwrite",
      "delete_permissions": "delete_channel_permission_overwrite",
      "stage_instance": "get_stage_instance",
      "end_stage": "delete_stage_instance",
      "edit_stage": "update_stage_instance",
      "set_voice_status": "update_voice_channel_status",
      "send_soundboard_sound": "send_soundboard_sound",
    },
    links={"message": ("MessageRef", ("message_id",))},
  ),
  "MessageRef": RefSpec(
    ("channel_id", "message_id"),
    "A message by channel and id.",
    {
      "get": "get_message",
      "edit": "update_message",
      "delete": "delete_message",
      "crosspost": "crosspost_message",
      "pin": "create_pin",
      "unpin": "delete_pin",
      "react": "add_my_message_reaction",
      "unreact": "delete_my_message_reaction",
      "remove_reaction": "delete_user_message_reaction",
      "clear_reactions": "delete_all_message_reactions",
      "clear_reaction": "delete_all_message_reactions_by_emoji",
      "reactions": "list_message_reactions_by_emoji",
      "start_thread": "create_thread_from_message",
      "poll_voters": "get_answer_voters",
      "end_poll": "poll_expire",
      "reply": (
        "create_message",
        {"message_reference": '{"message_id": self.message_id}'},
      ),
    },
  ),
  "GuildRef": RefSpec(
    ("guild_id",),
    "A server by id.",
    {
      "get": "get_guild",
      "edit": "update_guild",
      "leave": "leave_guild",
      "preview": "get_guild_preview",
      "channels": "list_guild_channels",
      "create_channel": "create_guild_channel",
      "reorder_channels": "bulk_update_guild_channels",
      "members": "list_guild_members",
      "search_members": "search_guild_members",
      "bans": "list_guild_bans",
      "ban": "ban_user_from_guild",
      "unban": "unban_user_from_guild",
      "get_ban": "get_guild_ban",
      "bulk_ban": "bulk_ban_users_from_guild",
      "roles": "list_guild_roles",
      "create_role": "create_guild_role",
      "reorder_roles": "bulk_update_guild_roles",
      "role_member_counts": "guild_role_member_counts",
      "emojis": "list_guild_emojis",
      "create_emoji": "create_guild_emoji",
      "stickers": "list_guild_stickers",
      "create_sticker": "create_guild_sticker",
      "events": "list_guild_scheduled_events",
      "create_event": "create_guild_scheduled_event",
      "invites": "list_guild_invites",
      "webhooks": "get_guild_webhooks",
      "audit_log": "list_guild_audit_log_entries",
      "prune_preview": "preview_prune_guild",
      "prune": "prune_guild",
      "active_threads": "get_active_guild_threads",
      "voice_regions": "list_guild_voice_regions",
      "vanity_url": "get_guild_vanity_url",
      "welcome_screen": "get_guild_welcome_screen",
      "edit_welcome_screen": "update_guild_welcome_screen",
      "widget_settings": "get_guild_widget_settings",
      "edit_widget_settings": "update_guild_widget_settings",
      "widget": "get_guild_widget",
      "onboarding": "get_guilds_onboarding",
      "edit_onboarding": "put_guilds_onboarding",
      "automod_rules": "list_auto_moderation_rules",
      "create_automod_rule": "create_auto_moderation_rule",
      "automod_rule": "get_auto_moderation_rule",
      "edit_automod_rule": "update_auto_moderation_rule",
      "delete_automod_rule": "delete_auto_moderation_rule",
      "soundboard_sounds": "list_guild_soundboard_sounds",
      "create_soundboard_sound": "create_guild_soundboard_sound",
      "templates": "list_guild_templates",
      "create_template": "create_guild_template",
      "integrations": "list_guild_integrations",
      "delete_integration": "delete_guild_integration",
      "commands": "list_guild_application_commands",
      "create_command": "create_guild_application_command",
      "set_commands": "bulk_set_guild_application_commands",
      "command_permissions": "list_guild_application_command_permissions",
      "incident_actions": "update_guild_incident_actions",
      "search": "guild_search",
      "join_requests": "get_guild_join_requests",
    },
    links={
      "member": ("MemberRef", ("user_id",)),
      "role": ("RoleRef", ("role_id",)),
      "emoji": ("EmojiRef", ("emoji_id",)),
      "sticker": ("StickerRef", ("sticker_id",)),
      "event": ("ScheduledEventRef", ("event_id",)),
    },
  ),
  "MemberRef": RefSpec(
    ("guild_id", "user_id"),
    "A member of a server by guild and user id.",
    {
      "get": "get_guild_member",
      "edit": "update_guild_member",
      "kick": "delete_guild_member",
      "ban": "ban_user_from_guild",
      "unban": "unban_user_from_guild",
      "add_role": "add_guild_member_role",
      "remove_role": "delete_guild_member_role",
      "voice_state": "get_voice_state",
      "set_voice_state": "update_voice_state",
    },
    mixin="_MemberExtras",
  ),
  "RoleRef": RefSpec(
    ("guild_id", "role_id"),
    "A role by guild and id.",
    {
      "get": "get_guild_role",
      "edit": "update_guild_role",
      "delete": "delete_guild_role",
    },
  ),
  "UserRef": RefSpec(
    ("user_id",),
    "A user by id.",
    {"get": "get_user", "dm": ("create_dm", {"recipient_id": "self.user_id"})},
    mixin="_UserExtras",
  ),
  "EmojiRef": RefSpec(
    ("guild_id", "emoji_id"),
    "A custom emoji by guild and id.",
    {
      "get": "get_guild_emoji",
      "edit": "update_guild_emoji",
      "delete": "delete_guild_emoji",
    },
  ),
  "StickerRef": RefSpec(
    ("guild_id", "sticker_id"),
    "A custom sticker by guild and id.",
    {
      "get": "get_guild_sticker",
      "edit": "update_guild_sticker",
      "delete": "delete_guild_sticker",
    },
  ),
  "ScheduledEventRef": RefSpec(
    ("guild_id", "event_id"),
    "A scheduled event by guild and id.",
    {
      "get": "get_guild_scheduled_event",
      "edit": "update_guild_scheduled_event",
      "delete": "delete_guild_scheduled_event",
      "users": "list_guild_scheduled_event_users",
      "count_users": "count_guild_scheduled_event_users",
    },
  ),
  "WebhookRef": RefSpec(
    ("webhook_id",),
    "A webhook by id (needs a bot with the right permissions).",
    {"get": "get_webhook", "edit": "update_webhook", "delete": "delete_webhook"},
    links={"with_token": ("WebhookTokenRef", ("webhook_token",))},
  ),
  "WebhookTokenRef": RefSpec(
    ("webhook_id", "webhook_token"),
    "A webhook by id and token: what its url holds, and what an interaction's followups use.",
    {
      "get": "get_webhook_by_token",
      "edit": "update_webhook_by_token",
      "delete": "delete_webhook_by_token",
      "execute": "execute_webhook",
      "message": "get_webhook_message",
      "edit_message": "update_webhook_message",
      "delete_message": "delete_webhook_message",
      "original_message": "get_original_webhook_message",
      "edit_original_message": "update_original_webhook_message",
      "delete_original_message": "delete_original_webhook_message",
    },
  ),
  "InviteRef": RefSpec(
    ("code",),
    "An invite by code.",
    {"get": "invite_resolve", "revoke": "invite_revoke"},
  ),
  "CommandRef": RefSpec(
    ("application_id", "command_id"),
    "An application command by application and id.",
    {
      "get": "get_application_command",
      "edit": "update_application_command",
      "delete": "delete_application_command",
    },
  ),
}


def ref_method(
  spec: RefSpec, name: str, entry: str | tuple[str, dict[str, str]]
) -> str:
  op_id, fixed = (entry, {}) if isinstance(entry, str) else entry
  sh = shape(typing.cast("Any", HTTP_OPERATIONS)[op_id])
  bound = {
    n: spec_id for n, wire, _ in sh.path for spec_id in spec.ids if spec_id == wire
  }
  assert bound or fixed, f"{name}: {op_id} has none of the ref's ids {spec.ids}"
  positional = [f"{n}: {ann}" for n, _, ann in sh.path if n not in bound]
  if sh.root_body is not None:
    positional.append(f"body: {sh.root_body}")
  positional += [f"{n}: {a} = UNSET" for n, a in sh.lead if n not in fixed]
  keywords = [f"{n}: {a}" for n, a in sh.required if n not in fixed] + [
    f"{n}: {a} = UNSET" for n, a in sh.optional if n not in fixed
  ]
  extras = extras_of(sh)
  star = ["*"] if (keywords or extras) else []
  signature = ",\n    ".join(["self", *positional, *star, *keywords, *extras])
  args: list[str] = []
  for n, wire, _ in sh.path:
    args.append(f"self.{bound[n]}" if n in bound else n)
  if sh.root_body is not None:
    args.append("body")
  kwargs = [f"{n}={fixed[n]}" if n in fixed else f"{n}={n}" for n in sh.keyword_names]
  kwargs += [e.split(":")[0] + "=" + e.split(":")[0] for e in extras]
  call = ", ".join([*args, *kwargs])
  doc = f"{sh.op.method} {sh.op.path}"
  return (
    f"  async def {name}(\n    {signature},\n  ) -> {sh.returns}:\n"
    f'    """{doc}"""\n'
    f"    return await self.api.{op_id}({call})\n"
  )


def ref_class(name: str, spec: RefSpec) -> str:
  base = f"({spec.mixin})" if spec.mixin else ""
  fields = "\n".join(f"  {i}: str" for i in spec.ids)
  out = [
    "@dataclass(frozen=True, slots=True)",
    f"class {name}{base}:",
    f'  """{spec.doc}"""',
    "",
    "  api: DiscordAPI",
    fields,
    "",
  ]
  for link, (target, extra_ids) in spec.links.items():
    params = ", ".join(f"{i}: int | str" for i in extra_ids)
    carried = ", ".join(f"self.{i}" for i in spec.ids)
    given = ", ".join(f"str({i})" for i in extra_ids)
    out += [
      f"  def {link}(self, {params}) -> {target}:",
      f'    """The {target[:-3].lower()} with this id."""',
      f"    return {target}(self.api, {carried}, {given})",
      "",
    ]
  for method_name, entry in spec.methods.items():
    out.append(ref_method(spec, method_name, entry))
  return "\n".join(out)


def refs_module() -> str:
  out = [
    "# Generated by scripts/gen_api.py. Do not edit.",
    '"""Discord objects by id, with their ids bound: `api.channel(5).send(content="hi")`.',
    "",
    "Each ref is a handle (nothing is fetched). Its methods are the flat API's with the",
    "ref's ids filled in; anything else is on `ref.api`.",
    '"""',
    "",
    "from collections.abc import Mapping, Sequence",
    "from dataclasses import dataclass",
    "from datetime import datetime",
    "from typing import TYPE_CHECKING, Any, Literal",
    "",
    "from micro.discord._api import UNSET, Upload",
    "from micro.discord._refs import _MemberExtras, _UserExtras",
    "from micro.discord.models import http as m",
    "from micro.discord.ui import AllowedMentions, Buildable, Emoji",
    "",
    "if TYPE_CHECKING:",
    "  from micro.discord.api import DiscordAPI",
    "",
    "",
  ]
  for name, spec in REFS.items():
    out.append(ref_class(name, spec))
    out.append("")
  out.append("__all__ = (" + ", ".join(f'"{n}"' for n in REFS) + ")")
  return "\n".join(out) + "\n"


def main() -> None:
  out = [
    "# Generated by scripts/gen_api.py from Discord's OpenAPI specification. Do not edit.",
    '"""Every Discord operation as one method: `await api.create_message(channel_id, content="hi")`."""',
    "",
    "from collections.abc import Mapping, Sequence",
    "from datetime import datetime",
    "from typing import Any, Literal",
    "",
    "from micro.discord._api import UNSET, ApiBase, Upload",
    "from micro.discord.models import http as m",
    "from micro.discord.ui import AllowedMentions, Buildable, Emoji",
    "",
    "",
    "class DiscordAPI(ApiBase):",
    '  """Path parameters are positional, the rest keywords; `reason=` goes to the audit log,',
    "  `files=[Upload(...)]` attaches files. Unpassed arguments are left out of the request,",
    '  and passing None sends null."""',
    "",
  ]
  for op in HTTP_OPERATIONS.values():
    out.append(method(op))
  out += ["", '__all__ = ("DiscordAPI", "Upload")', ""]
  OUT.write_text("\n".join(out))
  REFS_OUT.write_text(refs_module())
  count = sum(len(spec.methods) + len(spec.links) for spec in REFS.values())
  print(
    f"wrote api.py ({len(HTTP_OPERATIONS)} operations) and refs.py ({len(REFS)} refs, {count} methods)"
  )


if __name__ == "__main__":
  main()
