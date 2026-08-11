import asyncio
from collections.abc import Sequence
from typing import Any

import hikari
from pydantic import BaseModel, JsonValue, SecretStr, ValidationError
from pydantic_core import to_json
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from micro._microservices import (
  DiscordCredential,
  GatewayAssignment,
  GatewayIdentify,
  GuildMembersRequest,
  Microservice,
  PresenceUpdate,
  VoiceStateUpdate,
  request_content_type,
)
from micro.queue import QueueClient

from ._connection import ShardConnection
from ._events import ConnectionEvent, ConnectionSink, Dispatch, DispatchSink
from ._runner import event_loop_factory


class Gateway(Microservice):
  """ASGI coordinator for independently managed Discord shard connections."""

  def __init__(
    self,
    token: str | None = None,
    *,
    intents: hikari.Intents,
    dispatch: DispatchSink | None = None,
    connection: ConnectionSink | None = None,
    shard_ids: Sequence[int] | None = None,
    shard_count: int | None = None,
  ) -> None:
    if token == "":
      raise ValueError("token cannot be empty.")
    initial_shards, initial_count = _validate_shards(shard_ids, shard_count)
    if token is not None and initial_count is None:
      initial_count = 1
      initial_shards = (0,)
    if initial_count is not None and initial_shards is None:
      initial_shards = tuple(range(initial_count))
    self.queue = QueueClient()
    self.intents = intents
    self._uses_queue_dispatch = dispatch is None
    self._dispatch_sink = dispatch
    self._connection_sink = connection
    self._shards: dict[int, ShardConnection] = {}
    self._shard_count = initial_count
    self._assignment_revision = -1
    self._credential_revision = -1
    self._credential: str | None = None
    self._topology_ready = asyncio.Event()
    self._standalone = token is not None and initial_count is not None
    self._startup: asyncio.Task[None] | None = None
    super().__init__("gateway")
    for path, endpoint in (
      ("/gateway/presence", self._update_presence),
      ("/gateway/guild-members", self._request_guild_members),
      ("/gateway/voice-state", self._update_voice_state),
      ("/gateway/assignment", self._assignment_endpoint),
      ("/discord/credential", self._credential_endpoint),
    ):
      self.add_route(path, endpoint, methods=("POST",), name=path[1:].replace("/", ":"))
    self.add_route(
      "/gateway/connections/{shard_id}/identify",
      self._identify_endpoint,
      methods=("POST",),
      name="gateway:identify",
    )
    if token is not None:
      self._set_credential(DiscordCredential(token=SecretStr(token), revision=0))
    if initial_count is not None:
      self._reconcile_assignment(
        GatewayAssignment(
          revision=0,
          shard_count=initial_count,
          shard_ids=initial_shards or (),
          publish_shard_ids=initial_shards or (),
        )
      )

  @property
  def service(self) -> Microservice:
    return self

  @property
  def shard_ids(self) -> tuple[int, ...]:
    return tuple(self._shards)

  @property
  def shard_count(self) -> int | None:
    return self._shard_count

  @property
  def credential(self) -> str:
    if self._credential is None:
      raise RuntimeError("Discord credential is not configured.")
    return self._credential

  @property
  def component_ready(self) -> bool:
    topology_ready = not self._uses_queue_dispatch or self._topology_ready.is_set()
    return (
      topology_ready
      and self._credential is not None
      and self._assignment_revision >= 0
      and all(shard.started for shard in self._shards.values())
    )

  def apply_state(self, state: JsonValue) -> None:
    self.queue.apply_state(state)
    self._topology_ready.set()

  def schema_document(self, root_path: str) -> dict[str, JsonValue]:
    document = super().schema_document(root_path)
    document.update(
      service="micro.gateway",
      events=[],
      requests=[],
      shard_ids=list(self._shards),
      shard_count=self.shard_count,
    )
    return document

  async def start(self) -> None:
    if self._standalone:
      self._startup = asyncio.create_task(
        self._start_standalone(), name="micro.gateway.start"
      )

  async def _start_standalone(self) -> None:
    if self._uses_queue_dispatch:
      await self._topology_ready.wait()
    await asyncio.gather(*(shard.identify() for shard in self._shards.values()))

  async def close(self) -> None:
    if self._startup is not None:
      if not self._startup.done():
        self._startup.cancel()
      await asyncio.gather(self._startup, return_exceptions=True)
      self._startup = None
    await asyncio.gather(*(shard.stop() for shard in tuple(self._shards.values())))
    await self.queue.aclose()

  def run(self) -> None:
    try:
      with asyncio.Runner(loop_factory=event_loop_factory) as runner:
        runner.run(self._run_until_closed())
    except KeyboardInterrupt:
      pass

  async def _run_until_closed(self) -> None:
    try:
      await self.start()
      if self._startup is not None:
        await self._startup
      await asyncio.gather(*(shard.join() for shard in self._shards.values()))
    finally:
      await self.close()

  async def _credential_endpoint(self, request: Request) -> Response:
    credential = await _control_request(request, DiscordCredential)
    if isinstance(credential, Response):
      return credential
    try:
      changed = self._set_credential(credential)
      if changed:
        await asyncio.gather(*(shard.stop() for shard in self._shards.values()))
    except ValueError as exc:
      return JSONResponse({"detail": str(exc)}, status_code=409)
    return Response(status_code=204)

  def _set_credential(self, credential: DiscordCredential) -> bool:
    token = credential.token.get_secret_value()
    if credential.revision < self._credential_revision:
      raise ValueError("Discord credential revision is stale.")
    if credential.revision == self._credential_revision:
      if token != self._credential:
        raise ValueError("A revision cannot identify two Discord credentials.")
      return False
    changed = self._credential is not None and token != self._credential
    self._credential = token
    self._credential_revision = credential.revision
    return changed

  async def _assignment_endpoint(self, request: Request) -> Response:
    assignment = await _control_request(request, GatewayAssignment)
    if isinstance(assignment, Response):
      return assignment
    try:
      await self._apply_assignment(assignment)
    except ValueError as exc:
      return JSONResponse({"detail": str(exc)}, status_code=409)
    return Response(status_code=204)

  async def _apply_assignment(self, assignment: GatewayAssignment) -> None:
    if assignment.revision < self._assignment_revision:
      raise ValueError("Gateway assignment revision is stale.")
    if assignment.revision == self._assignment_revision:
      current = GatewayAssignment(
        revision=assignment.revision,
        shard_count=self._shard_count or assignment.shard_count,
        shard_ids=tuple(self._shards),
        publish_shard_ids=tuple(
          shard_id for shard_id, shard in self._shards.items() if shard.may_publish
        ),
      )
      if current != assignment:
        raise ValueError("A revision cannot identify two Gateway assignments.")
      return
    await self._reconcile_assignment_async(assignment)

  def _reconcile_assignment(self, assignment: GatewayAssignment) -> None:
    self._assignment_revision = assignment.revision
    self._shard_count = assignment.shard_count
    for shard_id in assignment.shard_ids:
      self._shards[shard_id] = ShardConnection(self, shard_id, assignment.shard_count)
    for shard_id in assignment.publish_shard_ids:
      self._shards[shard_id].may_publish = True
    if self._credential is not None:
      for shard in self._shards.values():
        shard.prepare()

  async def _reconcile_assignment_async(self, assignment: GatewayAssignment) -> None:
    desired = set(assignment.shard_ids)
    removed = [
      shard
      for shard_id, shard in self._shards.items()
      if shard_id not in desired or shard.shard_count != assignment.shard_count
    ]
    await asyncio.gather(*(shard.stop() for shard in removed))
    for shard in removed:
      self._shards.pop(shard.shard_id, None)
    for shard_id in assignment.shard_ids:
      self._shards.setdefault(
        shard_id, ShardConnection(self, shard_id, assignment.shard_count)
      )
    publishing = set(assignment.publish_shard_ids)
    for shard_id, shard in self._shards.items():
      shard.may_publish = shard_id in publishing
      if self._credential is not None:
        shard.prepare()
    self._shard_count = assignment.shard_count
    self._assignment_revision = assignment.revision

  async def _identify_endpoint(self, request: Request) -> Response:
    command = await _control_request(request, GatewayIdentify)
    if isinstance(command, Response):
      return command
    try:
      path_shard = int(request.path_params["shard_id"])
      if path_shard != command.shard_id:
        raise ValueError("Identify path and body shard IDs differ.")
      if command.assignment_revision != self._assignment_revision:
        raise ValueError("Identify command targets a stale assignment.")
      shard = self._shards[command.shard_id]
      await shard.identify()
    except (KeyError, ValueError) as exc:
      return JSONResponse({"detail": str(exc)}, status_code=409)
    return Response(status_code=204)

  async def publish_dispatch(self, dispatch: Dispatch, *, application: bool) -> None:
    if application:
      if self._dispatch_sink is not None:
        await self._dispatch_sink(dispatch)
      else:
        await self.queue.publish(
          "gateway.events", to_json((dispatch.name, dispatch.payload))
        )
    if self._uses_queue_dispatch:
      await self.queue.publish(
        "gateway.projection",
        to_json(
          (
            "event",
            dispatch.connection_id,
            dispatch.shard_id,
            dispatch.name,
            dispatch.payload,
          )
        ),
      )

  async def report_connection(self, event: ConnectionEvent) -> None:
    if self._uses_queue_dispatch:
      await self.queue.publish(
        "gateway.projection",
        to_json(("connection", event.kind, event.shard_id, event.connection_id)),
      )
    if self._connection_sink is not None:
      await self._connection_sink(event)

  async def _update_presence(self, request: Request) -> Response:
    update = await _control_request(request, PresenceUpdate)
    if isinstance(update, Response):
      return update
    activity = (
      hikari.Activity(
        name=update.activity.name,
        type=hikari.ActivityType(update.activity.type),
        url=update.activity.url,
        state=update.activity.state,
      )
      if update.activity is not None
      else None
    )
    await asyncio.gather(
      *(
        shard.bot.update_presence(
          status=hikari.Status(update.status),
          idle_since=update.idle_since,
          activity=activity,
          afk=update.afk,
        )
        for shard in self._shards.values()
        if shard.started and shard.bot is not None
      )
    )
    return Response(status_code=204)

  async def _request_guild_members(self, request: Request) -> Response:
    members = await _control_request(request, GuildMembersRequest)
    if isinstance(members, Response):
      return members
    shard = self._shard_for_guild(members.guild_id)
    kwargs: dict[str, Any] = {
      "include_presences": members.include_presences,
      "limit": members.limit,
    }
    if members.query is not None:
      kwargs["query"] = members.query
    if members.users is not None:
      kwargs["users"] = members.users
    if members.nonce is not None:
      kwargs["nonce"] = members.nonce
    assert shard.bot is not None
    await shard.bot.request_guild_members(members.guild_id, **kwargs)
    return Response(status_code=204)

  async def _update_voice_state(self, request: Request) -> Response:
    update = await _control_request(request, VoiceStateUpdate)
    if isinstance(update, Response):
      return update
    shard = self._shard_for_guild(update.guild_id)
    assert shard.bot is not None
    await shard.bot.update_voice_state(
      update.guild_id,
      update.channel_id,
      self_mute=update.self_mute,
      self_deaf=update.self_deaf,
    )
    return Response(status_code=204)

  def _shard_for_guild(self, guild_id: int) -> ShardConnection:
    candidates = [shard for shard in self._shards.values() if shard.started]
    if not candidates:
      raise RuntimeError("No active Gateway shard is available.")
    shard_count = candidates[0].shard_count
    shard_id = (guild_id >> 22) % shard_count
    try:
      shard = self._shards[shard_id]
    except KeyError as exc:
      raise RuntimeError("This Gateway does not own the guild's shard.") from exc
    if not shard.started or shard.bot is None:
      raise RuntimeError("The guild's Gateway shard is not active.")
    return shard


def _validate_shards(
  shard_ids: Sequence[int] | None,
  shard_count: int | None,
) -> tuple[tuple[int, ...] | None, int | None]:
  if shard_count is not None and (
    isinstance(shard_count, bool)
    or not isinstance(shard_count, int)
    or not 1 <= shard_count <= 4096
  ):
    raise ValueError("shard_count must be between 1 and 4096.")
  if shard_ids is None:
    return None, shard_count
  if shard_count is None:
    raise ValueError("shard_count is required when shard_ids are specified.")
  normalized = tuple(dict.fromkeys(shard_ids))
  if any(
    isinstance(shard_id, bool)
    or not isinstance(shard_id, int)
    or not 0 <= shard_id < shard_count
    for shard_id in normalized
  ):
    raise ValueError("Every shard ID must be between 0 and shard_count - 1.")
  if not normalized:
    raise ValueError("shard_ids cannot be empty.")
  return normalized, shard_count


async def _control_request[ModelT: BaseModel](
  request: Request, model: type[ModelT]
) -> ModelT | Response:
  if request_content_type(request) != "application/json":
    return JSONResponse(
      {"detail": "Gateway control requests require application/json."},
      status_code=415,
    )
  try:
    return model.model_validate_json(await request.body())
  except ValidationError as exc:
    return JSONResponse(
      {
        "detail": "Gateway control request does not match its schema.",
        "errors": exc.errors(include_url=False),
      },
      status_code=422,
    )
