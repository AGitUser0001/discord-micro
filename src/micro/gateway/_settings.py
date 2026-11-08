"""The Gateway's configuration: one shared document (see `micro.config`)."""

from pydantic import BaseModel, ConfigDict, Field

from ._control import PresenceUpdate

SETTINGS_NAME = "gateway"
"""The name of the Gateway's shared `Config` table."""


class GatewaySettings(BaseModel):
  """Everything about how the Gateway runs, except the token and where NATS is.

  Every Gateway worker follows this document. Change it with `micro configure`,
  `GatewayControl`, or any other writer of the `gateway` config table. A change to
  `shard_count` or `intents` makes the workers connect a new generation beside the old
  one, which takes over only once every shard is READY.
  """

  model_config = ConfigDict(frozen=True, extra="ignore")

  shard_count: int = Field(default=1, ge=1, le=4096)
  """How many shards the bot is split into."""
  intents: str = "unprivileged"
  """Gateway intents: names or numbers, comma separated (`unprivileged,message_content`)."""
  max_concurrency: int = Field(default=1, ge=1)
  """Identifies Discord allows per 5 seconds."""
  lease_ttl: float = Field(default=10.0, ge=3)
  """Seconds a shard lease lives without renewal."""
  presence: PresenceUpdate | None = None
  """The bot's status and activity, applied to every shard; None leaves Discord's default."""
