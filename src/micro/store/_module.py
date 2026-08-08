from pydantic import BaseModel, ConfigDict, Field, field_validator


class GraphModule(BaseModel):
  """A serializable contribution to a Micro graph schema."""

  model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

  id: str = Field(min_length=1)
  graphql_schema: str = Field(alias="schema", min_length=1)

  @field_validator("id")
  @classmethod
  def _id_has_no_whitespace(cls, value: str) -> str:
    if any(character.isspace() for character in value):
      raise ValueError("graph module IDs cannot contain whitespace")
    return value


# Transitional names for applications written against the initial store API.
GraphQLModule = GraphModule
StoreModule = GraphModule
