from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ActivityUpdate(BaseModel):
  model_config = ConfigDict(extra="forbid", frozen=True)

  name: str = Field(min_length=1)
  type: Literal[0, 1, 2, 3, 4, 5] = 0
  url: str | None = None
  state: str | None = None


class PresenceUpdate(BaseModel):
  model_config = ConfigDict(extra="forbid", frozen=True)

  status: Literal["online", "idle", "dnd", "offline"] = "online"
  idle_since: datetime | None = None
  activity: ActivityUpdate | None = None
  afk: bool = False


class GuildMembersRequest(BaseModel):
  model_config = ConfigDict(extra="forbid", frozen=True)

  guild_id: int = Field(gt=0)
  include_presences: bool = False
  query: str | None = None
  limit: int = Field(default=0, ge=0, le=1000)
  users: tuple[int, ...] | None = None
  nonce: str | None = Field(default=None, max_length=32)

  @model_validator(mode="after")
  def _one_filter(self) -> GuildMembersRequest:
    if self.query is not None and self.users is not None:
      raise ValueError("query and users are mutually exclusive")
    if self.users is not None and not self.users:
      raise ValueError("users cannot be empty")
    return self


class VoiceStateUpdate(BaseModel):
  model_config = ConfigDict(extra="forbid", frozen=True)

  guild_id: int = Field(gt=0)
  channel_id: int | None = Field(default=None, gt=0)
  self_mute: bool = False
  self_deaf: bool = False
