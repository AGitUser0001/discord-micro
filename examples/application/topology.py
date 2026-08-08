from micro.client import ServiceClient
from micro.service import JsonValue


class ApplicationTopology:
  """Consumes ordinary service routes plus the application's graph-store route."""

  def __init__(self, services: ServiceClient) -> None:
    self.services = services
    self.store_url: str | None = None

  def apply_state(self, state: JsonValue) -> None:
    if not isinstance(state, dict):
      raise TypeError("Application topology must be an object.")
    stores = state.get("stores")
    if not isinstance(stores, list) or len(stores) != 1:
      raise ValueError("This example expects exactly one graph store.")
    store = stores[0]
    if not isinstance(store, dict):
      raise TypeError("The graph store route must be an object.")
    base_url = store.get("base_url")
    if not isinstance(base_url, str):
      raise TypeError("The graph store needs a base_url.")

    self.services.apply_state(state)
    self.store_url = base_url.rstrip("/")
