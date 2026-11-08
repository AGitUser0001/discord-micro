"""Gateway settings that can live on the network (see `micro.config`)."""

from pydantic import BaseModel, ConfigDict, Field

SETTINGS_NAME = "gateway"
"""The name of the Gateway's shared `Config`."""


class GatewaySettings(BaseModel):
  """What every Gateway worker follows when it runs with `networked=True`.

  The token and the NATS address are not here: they are needed before NATS is reachable
  and stay in each process's environment. Intents are not here either: they belong to the
  Gateway generation and are changed only with `GatewayControl.set_intents`.
  """

  model_config = ConfigDict(frozen=True, extra="ignore")

  max_concurrency: int = Field(default=1, ge=1)
  """Identifies Discord allows per 5 seconds."""
  lease_ttl: float = Field(default=10.0, ge=3)
  """Seconds a shard lease lives without renewal."""
