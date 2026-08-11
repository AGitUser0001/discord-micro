from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator
from pydantic_core import to_json


class DiscordCredential(BaseModel):
  """The single Discord identity managed by a Micro deployment."""

  model_config = ConfigDict(extra="forbid", frozen=True)

  token: SecretStr
  revision: int = Field(ge=0)

  @field_validator("token")
  @classmethod
  def _token_not_empty(cls, value: SecretStr) -> SecretStr:
    if not value.get_secret_value():
      raise ValueError("token cannot be empty")
    return value

  def wire_bytes(self) -> bytes:
    """Serialize for the trusted management connection without redaction."""
    return to_json({"token": self.token.get_secret_value(), "revision": self.revision})
