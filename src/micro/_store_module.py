from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StoreModule(BaseModel):
  """A serializable extension distributed from the overseer to graph stores."""

  model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

  id: str = Field(min_length=1)
  graphql_schema: str = Field(alias="schema", min_length=1)
  configuration: dict[str, Any] = Field(default_factory=dict)

  @field_validator("id")
  @classmethod
  def _id_has_no_whitespace(cls, value: str) -> str:
    if any(character.isspace() for character in value):
      raise ValueError("store module IDs cannot contain whitespace")
    return value
