from schemas import GREETING_STORE
from starlette.applications import Starlette
from starlette.routing import Mount

from micro.overseer import NetworkDiscovery, Overseer
from micro.schemas.discord_http import DISCORD_HTTP_RATE_LIMITS
from micro.schemas.gateway import GATEWAY_PROJECTION

discovery = NetworkDiscovery()
overseer = Overseer(
  discovery,
  modules=(GREETING_STORE, GATEWAY_PROJECTION, DISCORD_HTTP_RATE_LIMITS),
)

# A production host would normally put authentication around these control routes.
app = Starlette(
  routes=[
    Mount("/discovery", discovery),
    Mount("/", overseer),
  ]
)
