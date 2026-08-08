from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from micro.overseer import GraphModule
from micro.service import EventSchema, RequestSchema


class GreetingInput(BaseModel):
  model_config = ConfigDict(extra="forbid")

  name: Annotated[str, Field(min_length=1)]


class GreetingOutput(BaseModel):
  message: str


class AuditEntry(BaseModel):
  model_config = ConfigDict(extra="forbid")

  action: str
  subject: str


GREET = RequestSchema[GreetingInput, GreetingOutput](
  id="example.greet",
  input=GreetingInput,
  output=GreetingOutput,
)

AUDIT = EventSchema[AuditEntry](
  id="example.audit",
  payload=AuditEntry,
)

GREETING_STORE = GraphModule(
  id="example.greetings",
  schema="""
    type Greeting @entity(key: ["name"]) {
      name: String!
      message: String!
    }

    type Query {
      greeting(name: String!): Greeting
        @from(key: "{'name': name}")
    }
  """,
)
