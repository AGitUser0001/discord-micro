"""A fake Discord, REST and Gateway, to run Micro end to end without a real bot.

    fake = FakeDiscord(token=TOKEN)
    api_url = await fake.start()      # point DISCORD_API_URL (or api_url=) at this
    await fake.dispatch("MESSAGE_CREATE", {...})
    await fake.stop()

The Gateway is a real websocket (HELLO, heartbeats, IDENTIFY, READY, GUILD_CREATE,
RESUME with replay, zlib and zstd stream compression), so hikari's own connection code
runs. The REST side covers the routes Micro uses and models a few of Discord's
rules: one callback per interaction, no edits or follow-ups before it, commands
unique per scope, and 50001 for guilds the bot is not in. Faults can be injected
per route to test retries and rate limits.
"""

import asyncio
import contextlib
import itertools
import json
import re
import time
import zlib
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from aiohttp import WSMsgType, web

API = "/api/v10"
_ids = itertools.count(1_000_000_000_000_000)


def snowflake() -> str:
  return str(next(_ids))


@dataclass
class Call:
  method: str
  path: str
  query: dict[str, str]
  body: Any
  status: int
  at: float = field(default_factory=time.monotonic)


@dataclass
class Fault:
  method: str | None
  pattern: re.Pattern[str]
  status: int
  body: dict[str, Any]
  headers: dict[str, str]
  times: int | None


@dataclass
class Session:
  id: str
  identify: dict[str, Any]
  seq: int = 0
  ws: web.WebSocketResponse | None = None
  compress: Callable[[bytes], bytes] | None = None
  buffer: list[tuple[int, str, Any]] = field(default_factory=list)


def _compressor(kind: str | None) -> Callable[[bytes], bytes] | None:
  """Transport compression for one connection: one stream context per connection."""
  if kind == "zlib-stream":
    stream = zlib.compressobj()
    return lambda data: stream.compress(data) + stream.flush(zlib.Z_SYNC_FLUSH)
  if kind == "zstd-stream":
    from compression import zstd

    encoder = zstd.ZstdCompressor()
    return lambda data: encoder.compress(data, zstd.ZstdCompressor.FLUSH_BLOCK)
  return None


def _error(status: int, code: int, message: str) -> web.Response:
  return web.json_response({"code": code, "message": message}, status=status)


class FakeDiscord:
  def __init__(
    self,
    token: str,
    *,
    application_id: str = "100",
    guilds: tuple[str, ...] = ("500",),
    heartbeat_ms: int = 3000,
  ) -> None:
    self.token = token
    self.application_id = application_id
    self.guilds = list(guilds)
    self.heartbeat_ms = heartbeat_ms
    self.calls: list[Call] = []
    self.commands: dict[str, list[dict[str, Any]]] = {}
    """Registered application commands by scope: "global" or a guild ID."""
    self.forbidden_guilds: set[str] = set()
    """Guild command routes answer 50001 (Missing Access) for these."""
    self.sessions: dict[str, Session] = {}
    self.identifies = 0
    self.members: dict[str, list[dict[str, Any]]] = {}
    """Members Discord returns for a guild when asked (op 8)."""
    self.member_requests: list[dict[str, Any]] = []
    self.resumes = 0
    self._faults: list[Fault] = []
    self._acked: set[str] = set()
    self._runner: web.AppRunner | None = None
    self.url = ""

  # Lifecycle -------------------------------------------------------------------

  async def start(self) -> str:
    app = web.Application()
    app.router.add_get("/gateway", self._gateway)
    app.router.add_route("*", API + "/{tail:.*}", self._rest)
    self._runner = web.AppRunner(app, access_log=None)
    await self._runner.setup()
    site = web.TCPSite(self._runner, "127.0.0.1", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]  # type: ignore[union-attr]
    self.url = f"http://127.0.0.1:{port}"
    return self.url + API

  async def stop(self) -> None:
    for session in self.sessions.values():
      if session.ws is not None and not session.ws.closed:
        with contextlib.suppress(Exception):
          await session.ws.close()
    if self._runner is not None:
      await self._runner.cleanup()

  # Test controls ---------------------------------------------------------------

  def fail(
    self,
    pattern: str,
    *,
    method: str | None = None,
    status: int = 500,
    body: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    times: int | None = 1,
  ) -> None:
    """Answer matching requests with this error (`times` None: until cleared)."""
    self._faults.append(
      Fault(
        method,
        re.compile(pattern),
        status,
        body or {"message": "injected fault", "code": 0},
        headers or {},
        times,
      )
    )

  def rate_limit(
    self, pattern: str, *, retry_after: float = 0.3, times: int = 1
  ) -> None:
    self.fail(
      pattern,
      status=429,
      body={
        "message": "You are being rate limited.",
        "retry_after": retry_after,
        "global": False,
      },
      headers={"Retry-After": str(retry_after), "X-RateLimit-Scope": "user"},
      times=times,
    )

  def clear_faults(self) -> None:
    self._faults.clear()

  def where(self, method: str, pattern: str) -> list[Call]:
    rule = re.compile(pattern)
    return [c for c in self.calls if c.method == method and rule.search(c.path)]

  async def until(self, check: Callable[[], bool], timeout: float = 10.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
      if check():
        return True
      await asyncio.sleep(0.05)
    return check()

  # Gateway ---------------------------------------------------------------------

  @property
  def connected(self) -> list[Session]:
    return [s for s in self.sessions.values() if s.ws is not None and not s.ws.closed]

  async def dispatch(self, name: str, data: dict[str, Any]) -> None:
    for session in self.connected:
      await self._dispatch(session, name, data)

  async def drop_gateway(self, code: int = 4000) -> None:
    """Close every connection the way Discord does for a resumable error."""
    for session in self.connected:
      assert session.ws is not None
      await session.ws.close(code=code)

  async def _send(
    self,
    session: Session,
    op: int,
    d: Any = None,
    t: str | None = None,
    s: int | None = None,
  ) -> None:
    assert session.ws is not None
    text = json.dumps({"op": op, "d": d, "t": t, "s": s})
    if session.compress is not None:
      await session.ws.send_bytes(session.compress(text.encode()))
    else:
      await session.ws.send_str(text)

  async def _dispatch(self, session: Session, name: str, data: Any) -> None:
    session.seq += 1
    session.buffer.append((session.seq, name, data))
    if session.ws is not None and not session.ws.closed:
      await self._send(session, 0, data, name, session.seq)

  async def _gateway(self, request: web.Request) -> web.StreamResponse:
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    scratch = Session(
      id="", identify={}, ws=ws, compress=_compressor(request.query.get("compress"))
    )
    await self._send(scratch, 10, {"heartbeat_interval": self.heartbeat_ms})
    session = scratch
    async for message in ws:
      if message.type not in (WSMsgType.TEXT, WSMsgType.BINARY):
        continue  # clients may send their JSON as text or as binary frames
      frame = json.loads(message.data)
      op = frame["op"]
      if op == 1:
        await self._send(session, 11)
      elif op == 2:
        d = frame["d"]
        if d.get("token") != self.token:
          await ws.close(code=4004)
          break
        self.identifies += 1
        session.id = snowflake()
        session.identify = d
        self.sessions[session.id] = session
        await self._ready(session)
      elif op == 8:
        d = frame["d"]
        self.member_requests.append(d)
        guild = str(d["guild_id"])
        await self._dispatch(
          session,
          "GUILD_MEMBERS_CHUNK",
          {
            "guild_id": guild,
            "members": self.members.get(guild, []),
            "chunk_index": 0,
            "chunk_count": 1,
            "nonce": d.get("nonce"),
          },
        )
      elif op == 6:
        d = frame["d"]
        known = self.sessions.get(d.get("session_id", ""))
        if known is None or d.get("seq", 0) > known.seq:
          await self._send(session, 9, False)
          continue
        self.resumes += 1
        known.ws, known.compress = ws, session.compress
        session = known
        for seq, name, data in [b for b in known.buffer if b[0] > d["seq"]]:
          await self._send(known, 0, data, name, seq)
        await self._dispatch(known, "RESUMED", {})
    if session.ws is ws:
      session.ws = None
    return ws

  async def _ready(self, session: Session) -> None:
    bot = {
      "id": self.application_id,
      "username": "fake-bot",
      "discriminator": "0",
      "avatar": None,
      "bot": True,
      "global_name": None,
    }
    await self._dispatch(
      session,
      "READY",
      {
        "v": 10,
        "user": bot,
        "guilds": [{"id": g, "unavailable": True} for g in self.guilds],
        "session_id": session.id,
        "resume_gateway_url": self.url.replace("http", "ws") + "/gateway",
        "shard": [0, 1],
        "application": {"id": self.application_id, "flags": 0},
      },
    )
    for guild in self.guilds:
      await self._dispatch(
        session,
        "GUILD_CREATE",
        {
          "id": guild,
          "name": f"guild-{guild}",
          "unavailable": False,
          "roles": [],
          "emojis": [],
          "stickers": [],
          "channels": [],
          "threads": [],
          "members": [],
          "presences": [],
          "voice_states": [],
          "stage_instances": [],
          "guild_scheduled_events": [],
          "member_count": 1,
          "large": False,
          "features": [],
        },
      )

  # REST ------------------------------------------------------------------------

  async def _rest(self, request: web.Request) -> web.Response:
    path = "/" + request.match_info["tail"]
    body: Any = None
    if request.can_read_body:
      raw = await request.read()
      body = json.loads(raw) if raw else None
    if request.headers.get("Authorization") != f"Bot {self.token}" and not self._public(
      path
    ):
      response = _error(401, 0, "401: Unauthorized")
    else:
      response = self._injected(request.method, path) or self._route(
        request.method, path, request.query, body
      )
    response.headers.setdefault("X-RateLimit-Limit", "5")
    response.headers.setdefault("X-RateLimit-Remaining", "4")
    response.headers.setdefault("X-RateLimit-Reset-After", "1.0")
    response.headers.setdefault("X-RateLimit-Bucket", re.sub(r"\d+", "{id}", path))
    self.calls.append(
      Call(request.method, path, dict(request.query), body, response.status)
    )
    return response

  def _public(self, path: str) -> bool:
    # Interaction callbacks and webhooks authenticate with their token in the path.
    return path.startswith(("/interactions/", "/webhooks/"))

  def _injected(self, method: str, path: str) -> web.Response | None:
    for fault in self._faults:
      if (fault.method in (None, method)) and fault.pattern.search(path):
        if fault.times is not None:
          fault.times -= 1
          if fault.times <= 0:
            self._faults.remove(fault)
        return web.json_response(fault.body, status=fault.status, headers=fault.headers)
    return None

  def _route(self, method: str, path: str, query: Any, body: Any) -> web.Response:
    if method == "GET" and path == "/gateway/bot":
      return web.json_response(
        {
          "url": self.url.replace("http", "ws") + "/gateway",
          "shards": 1,
          "session_start_limit": {
            "total": 1000,
            "remaining": 1000,
            "reset_after": 86_400_000,
            "max_concurrency": 1,
          },
        }
      )
    if method == "GET" and path in ("/oauth2/applications/@me", "/applications/@me"):
      return web.json_response(
        {"id": self.application_id, "name": "fake-bot", "flags": 0, "bot_public": True}
      )
    if method == "GET" and path == "/users/@me":
      return web.json_response(
        {
          "id": self.application_id,
          "username": "fake-bot",
          "discriminator": "0",
          "bot": True,
        }
      )

    if match := re.fullmatch(r"/applications/(\d+)/(?:guilds/(\d+)/)?commands", path):
      scope = match.group(2) or "global"
      if match.group(2) and (
        match.group(2) in self.forbidden_guilds or match.group(2) not in self.guilds
      ):
        return _error(403, 50001, "Missing Access")
      if method == "GET":
        return web.json_response(self.commands.get(scope, []))
      if method == "PUT":
        return self._overwrite(scope, body)

    callback = re.fullmatch(r"/interactions/(\d+)/([^/]+)/callback", path)
    if callback and method == "POST":
      token = callback.group(2)
      if token in self._acked:
        return _error(400, 40060, "Interaction has already been acknowledged.")
      self._acked.add(token)
      return web.Response(status=204)

    if match := re.fullmatch(r"/webhooks/(\d+)/([^/]+)(?:/messages/@original)?", path):
      token = match.group(2)
      if token not in self._acked:
        return _error(404, 10015, "Unknown Webhook")
      if method in ("PATCH", "POST"):
        return web.json_response(self._message(body or {}))
      if method == "DELETE":
        return web.Response(status=204)

    posted = re.fullmatch(r"/channels/(\d+)/messages", path)
    if posted and method == "POST":
      return web.json_response(self._message(body or {}, channel=posted.group(1)))

    return _error(404, 0, f"fake discord has no route for {method} {path}")

  def _message(self, body: dict[str, Any], channel: str = "600") -> dict[str, Any]:
    return {
      "id": snowflake(),
      "channel_id": channel,
      "content": body.get("content", ""),
      "author": {
        "id": self.application_id,
        "username": "fake-bot",
        "discriminator": "0",
        "avatar": None,
        "global_name": None,
        "bot": True,
      },
      "attachments": [],
      "embeds": body.get("embeds", []),
      "mentions": [],
      "mention_roles": [],
      "pinned": False,
      "mention_everyone": False,
      "tts": False,
      "timestamp": "2024-01-01T00:00:00+00:00",
      "edited_timestamp": None,
      "flags": 0,
      "type": 0,
    }

  def _overwrite(self, scope: str, body: Any) -> web.Response:
    if not isinstance(body, list):
      return _error(400, 50035, "Invalid Form Body")
    if len(body) > 100:
      return _error(400, 30032, "Maximum number of application commands reached (100)")
    seen: set[tuple[int, str]] = set()
    stored = []
    for command in body:
      kind, name = command.get("type", 1), command.get("name", "")
      if kind == 1 and not re.fullmatch(r"[a-z0-9_-]{1,32}", name):
        return _error(
          400, 50035, f"Invalid Form Body: name {name!r} is not a valid chat input name"
        )
      if (kind, name) in seen:
        return _error(400, 50035, f"Invalid Form Body: duplicate command {name!r}")
      seen.add((kind, name))
      stored.append(
        {
          "id": snowflake(),
          "application_id": self.application_id,
          "version": snowflake(),
          **command,
        }
      )
    self.commands[scope] = stored
    return web.json_response(stored)

  # Payload builders -------------------------------------------------------------

  def interaction(
    self,
    kind: int,
    data: dict[str, Any],
    *,
    guild: str | None = None,
    user: str = "700",
    **extra: Any,
  ) -> dict[str, Any]:
    guild = guild if guild is not None else self.guilds[0]
    person = {
      "id": user,
      "username": "tester",
      "discriminator": "0",
      "avatar": None,
      "global_name": None,
      "public_flags": 0,
    }
    return {
      "id": snowflake(),
      "token": f"tok{snowflake()}",
      "application_id": self.application_id,
      "version": 1,
      "type": kind,
      "data": data,
      "guild_id": guild,
      "channel_id": "600",
      "locale": "en-US",
      "member": {
        "user": person,
        "roles": [],
        "joined_at": "2024-01-01T00:00:00+00:00",
        "deaf": False,
        "mute": False,
        "flags": 0,
        "permissions": "0",
      },
      **extra,
    }

  def slash(
    self, name: str, options: list[dict[str, Any]] | None = None, **kw: Any
  ) -> dict[str, Any]:
    return self.interaction(
      2, {"id": snowflake(), "name": name, "type": 1, "options": options or []}, **kw
    )

  def component(self, custom_id: str, **kw: Any) -> dict[str, Any]:
    message = {**self._message({}), "id": snowflake()}
    return self.interaction(
      3, {"custom_id": custom_id, "component_type": 2}, message=message, **kw
    )

  def modal_submit(
    self, custom_id: str, fields: dict[str, str], **kw: Any
  ) -> dict[str, Any]:
    rows = [
      {"type": 1, "components": [{"type": 4, "custom_id": k, "value": v}]}
      for k, v in fields.items()
    ]
    return self.interaction(5, {"custom_id": custom_id, "components": rows}, **kw)

  def message_create(
    self, content: str, *, guild: str | None = None, author: str = "700"
  ) -> dict[str, Any]:
    return {
      **self._message({"content": content}, channel="600"),
      "guild_id": guild if guild is not None else self.guilds[0],
      "author": {
        "id": author,
        "username": "tester",
        "discriminator": "0",
        "avatar": None,
        "global_name": None,
        "public_flags": 0,
      },
      "member": {
        "roles": [],
        "joined_at": "2024-01-01T00:00:00+00:00",
        "deaf": False,
        "mute": False,
        "flags": 0,
      },
    }

  def acknowledge(self, payload: dict[str, Any]) -> None:
    """Treat an interaction as answered, as Discord does once its HTTP reply is sent."""
    self._acked.add(payload["token"])

  async def send(self, payload: dict[str, Any]) -> None:
    await self.dispatch("INTERACTION_CREATE", payload)
