from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from micro.overseer import StoreModule
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

GREETING_STORE = StoreModule(
  id="example.greetings",
  schema="""
    type Greeting {
      name: String!
      message: String!
    }

    extend type Query {
      greeting(name: String!): Greeting
    }

    extend type Mutation {
      saveGreeting(name: String!, message: String!): Greeting!
    }
  """,
  configuration={"operations": ["greeting", "saveGreeting"]},
)
