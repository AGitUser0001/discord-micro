from pydantic import BaseModel, ConfigDict


class DiscordModel(BaseModel):
  """Shared wire-safe configuration for generated Discord models."""

  model_config = ConfigDict(
    extra="allow",
    ser_json_bytes="base64",
    val_json_bytes="base64",
  )


__all__ = ("DiscordModel",)
