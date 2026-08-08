from schemas import GREETING_STORE
from starlette.applications import Starlette
from starlette.routing import Mount

from micro.overseer import NetworkDiscovery, Overseer

discovery = NetworkDiscovery()
overseer = Overseer(discovery, modules=(GREETING_STORE,))

# A production host would normally put authentication around these control routes.
app = Starlette(
  routes=[
    Mount("/discovery", discovery),
    Mount("/", overseer),
  ]
)
