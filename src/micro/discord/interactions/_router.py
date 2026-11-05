"""The interaction router: raw INTERACTION_CREATE in, one routed queue item out."""

import json
import logging
from collections.abc import Callable, Mapping
from typing import TYPE_CHECKING, Any, overload

from nats.js.errors import NotFoundError

from micro import subjects
from micro.discord.routes import AUTOCOMPLETE, interaction_route
from micro.service import DispatchSchema, Service

from ._flow import Flow, Middleware, Middlewares, flow_key
from ._templates import (
  INTERACTIONS_KEY,
  RESPONSE_DEADLINE,
  ensure_interactions_stream,
  report_failure,
  route_consumer,
)

if TYPE_CHECKING:
  from micro.discord import DiscordHTTPClient

logger = logging.getLogger("micro")

RAW_INTERACTION = DispatchSchema[dict[str, Any]](
  id="INTERACTION_CREATE", payload=dict[str, Any]
)
"""INTERACTION_CREATE as a plain mapping (no generated models loaded)."""

UNAVAILABLE = "This isn't available right now. Please try again in a moment."


class InteractionRouter(Service):
  """Splits interactions onto per-route work queues.

  For each raw INTERACTION_CREATE dispatch it computes the route (command name
  or custom_id prefix), checks that something can handle it, and enqueues it
  with a TTL of Discord's response deadline, deduplicated by interaction ID.
  Run any number of replicas. `use` adds middleware that runs before routing
  and may change the payload (unwrap a signed custom ID so it routes by its real
  prefix, drop or answer an interaction); override `route`, `owned`, or
  `unroutable` to change routing (by guild, A/B, allowlists, auditing).
  """

  def __init__(self, name: str = "interaction-router", **settings: Any) -> None:
    super().__init__(name, **settings)
    self._middleware = Middlewares()
    self._http: DiscordHTTPClient | None = None
    self.listen(RAW_INTERACTION)(self._on_interaction)

  @overload
  def use(self, scope: Middleware, /) -> Middleware: ...
  @overload
  def use(self, scope: str, function: Middleware, /) -> Middleware: ...
  @overload
  def use(self, scope: str, /) -> Callable[[Middleware], Middleware]: ...

  def use(self, scope: Middleware | str, function: Middleware | None = None, /) -> Any:
    """Add middleware ahead of routing: `use(fn)`, `use("scope", fn)`."""
    if function is None:
      return self._middleware.use(scope)  # type: ignore[arg-type]
    return self._middleware.use(scope, function)  # type: ignore[arg-type]

  async def on_start(self) -> None:
    await ensure_interactions_stream(self)
    await super().on_start()

  def route(self, payload: Mapping[str, Any]) -> str | None:
    """The route of an interaction (None drops it)."""
    return interaction_route(payload)

  async def owned(self, route: str) -> bool:
    """Whether a worker can take this route now.

    Presence answers the common case instantly; otherwise the route's consumer
    is asked whether any worker is currently pulling from it.
    """
    for entry in self.runtime.directory.entries("service"):
      routes = entry.metadata.get(INTERACTIONS_KEY)
      if isinstance(routes, list) and route in routes:
        return True
    try:
      info = await self.runtime.jetstream.consumer_info(
        subjects.INTERACTIONS_STREAM, route_consumer(route)
      )
    except NotFoundError:
      return False
    return (info.num_waiting or 0) > 0

  async def unroutable(self, payload: Mapping[str, Any]) -> None:
    """Answer an interaction nobody handles, so Discord does not time out."""
    from micro.discord import DiscordHTTPClient

    if payload.get("type") == AUTOCOMPLETE:
      body: dict[str, Any] = {"type": 8, "data": {"choices": []}}
    else:
      body = {
        "type": 4,
        "data": {
          "content": UNAVAILABLE,
          "flags": 1 << 6,
          "allowed_mentions": {"parse": []},
        },
      }
    await DiscordHTTPClient(self.runtime).call(
      "create_interaction_response",
      path={"interaction_id": payload["id"], "interaction_token": payload["token"]},
      body=body,
    )

  async def _on_interaction(self, payload: dict[str, Any]) -> None:
    from micro.discord import DiscordHTTPClient

    if self._http is None:
      self._http = DiscordHTTPClient(self.runtime)
    flow = Flow(payload, http=self._http, key=flow_key(payload), service=self)
    infrastructure: list[Exception] = []

    async def publish(flow: Flow) -> None:
      try:
        await self._publish(flow)
      except Exception as error:
        infrastructure.append(error)
        raise

    try:
      await self._middleware.run(flow, publish)
    except Exception as error:
      if infrastructure and error is infrastructure[0]:
        raise  # NATS trouble: let the event be redelivered
      logger.exception("Interaction middleware failed in %s", self.name)
      await report_failure(flow, error)

  async def _publish(self, flow: Flow) -> None:
    payload = flow.payload
    route = self.route(payload)
    if route is None:
      return
    if not await self.owned(route):
      logger.warning("No worker handles interaction route %s", route)
      try:
        await self.unroutable(payload)
      except Exception:
        logger.warning("Could not answer an unroutable interaction", exc_info=True)
      return
    await self.runtime.jetstream.publish(
      subjects.interaction(route),
      json.dumps(payload, separators=(",", ":")).encode(),
      stream=subjects.INTERACTIONS_STREAM,
      headers={"Nats-Msg-Id": str(payload.get("id"))},
      msg_ttl=RESPONSE_DEADLINE,
    )
