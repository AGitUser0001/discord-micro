"""Receive interactions over HTTP instead of the Gateway."""

import asyncio
import json
import os
from contextlib import suppress
from typing import Any

from micro import log, subjects
from micro._ed25519 import verify
from micro.runtime import Component

from ._context import REPLY_KEY

PING = 1
PONG = {"type": 1}


class InteractionEndpoint(Component):
  """Discord's "Interactions Endpoint URL": a replacement for the Gateway.

  Set the URL of this server in the developer portal. Each interaction is
  checked against your application's public key, published exactly like a
  Gateway INTERACTION_CREATE (so the router, commands, components, modals,
  middleware, and `CommandSync` work unchanged), and the request is held open
  until a handler gives its first response, which becomes the HTTP reply.
  Everything after that (follow-ups, edits) uses Discord's webhook endpoints
  as usual.

      components = ["micro.discord.interactions:InteractionEndpoint",
                    "micro.discord.interactions:InteractionRouter", ...]

  `public_key` defaults to `DISCORD_PUBLIC_KEY` (hex, from the developer portal).
  Any number of replicas can run behind one URL. Without the Gateway there are
  no events (messages, members, ...), so no member cache; commands, components
  and modals are all there is. Needs `micro[http]` (a web server).
  """

  kind = "interaction-endpoint"

  def __init__(
    self,
    *,
    public_key: str | None = None,
    host: str | None = None,
    port: int | None = None,
    path: str = "/interactions",
    name: str = "interaction-endpoint",
  ) -> None:
    super().__init__(name)
    key = public_key or os.environ.get("DISCORD_PUBLIC_KEY")
    if not key:
      raise ValueError(
        "A Discord public key is required (argument or DISCORD_PUBLIC_KEY)."
      )
    self._key = bytes.fromhex(key)
    self.host = host or os.environ.get("MICRO_HTTP_HOST", "127.0.0.1")
    self.port = (
      port if port is not None else int(os.environ.get("MICRO_HTTP_PORT", "8081"))
    )
    self.path = path
    self._server: Any = None

  async def on_start(self) -> None:
    """Start the web server and register this endpoint's URL in presence."""
    import uvicorn
    from starlette.applications import Starlette
    from starlette.routing import Route

    app = Starlette(routes=[Route(self.path, self.receive, methods=["POST"])])
    config = uvicorn.Config(
      app, host=self.host, port=self.port, log_level="warning", lifespan="off"
    )
    self._server = uvicorn.Server(config)
    self._server.install_signal_handlers = lambda: None
    serving = self.spawn(self._serve(), name="server")
    while not self._server.started:
      if serving.done():  # the port is taken, say: uvicorn gave up
        raise RuntimeError(
          f"The interaction endpoint could not listen on {self.host}:{self.port}."
        )
      await asyncio.sleep(0.01)
    await self.runtime.register(
      self, metadata={"url": f"http://{self.host}:{self.port}{self.path}"}
    )

  async def _serve(self) -> None:
    try:
      await self._server.serve()
    except SystemExit:  # uvicorn exits the process when it cannot bind
      pass

  async def on_close(self) -> None:
    """Stop the web server."""
    if self._server is not None:
      self._server.should_exit = True
      with suppress(Exception):
        await self._server.shutdown()

  def verified(self, signature: str | None, timestamp: str | None, body: bytes) -> bool:
    """Whether `signature` is a valid Ed25519 signature of `timestamp + body` for the public key."""
    if not signature or not timestamp:
      return False
    try:
      return verify(self._key, timestamp.encode() + body, bytes.fromhex(signature))
    except ValueError:
      return False

  async def receive(self, request: Any) -> Any:
    """Handle one POST from Discord: verify, publish, and wait for the first response."""
    from starlette.responses import JSONResponse, Response

    body = await request.body()
    if not await asyncio.to_thread(
      self.verified,
      request.headers.get("x-signature-ed25519"),
      request.headers.get("x-signature-timestamp"),
      body,
    ):
      return Response("invalid request signature", status_code=401)
    try:
      payload = json.loads(body)
    except ValueError:
      return Response("invalid body", status_code=400)
    if payload.get("type") == PING:
      return JSONResponse(PONG)
    async with self.tracked():
      reply = subjects.token(f"reply-{payload['id']}")
      subject = f"micro.discord.reply.{reply}"
      answers: asyncio.Queue[bytes] = asyncio.Queue(1)

      async def collect(message: Any) -> None:
        if answers.empty():
          answers.put_nowait(message.data)

      subscription = await self.runtime.nats.subscribe(subject, cb=collect)
      try:
        guild = payload.get("guild_id")
        await self.runtime.jetstream.publish(
          subjects.dispatch("INTERACTION_CREATE", guild),
          json.dumps({**payload, REPLY_KEY: subject}, separators=(",", ":")).encode(),
          stream=subjects.EVENTS_STREAM,
        )
        # No timeout of our own: Discord abandons the request after its 3 seconds,
        # and we stop waiting when it hangs up.
        answer = asyncio.ensure_future(answers.get())
        gone = asyncio.ensure_future(_disconnected(request))
        try:
          await asyncio.wait({answer, gone}, return_when=asyncio.FIRST_COMPLETED)
          if answer.done():
            return Response(answer.result(), media_type="application/json")
          log.warning(
            "Discord gave up on interaction %s before anything answered it",
            payload.get("id"),
          )
          return Response(status_code=504)
        finally:
          for task in (answer, gone):
            task.cancel()
      finally:
        with suppress(Exception):
          await subscription.unsubscribe()


async def _disconnected(request: Any) -> None:
  """Return once the client has hung up (the body has been read by now)."""
  while True:
    message = await request.receive()
    if message["type"] == "http.disconnect":
      return
