"""The messages greeter sends and receives."""

from typing import Annotated

from pydantic import BaseModel, Field

from micro.service import EventSchema, RequestSchema


class Greeting(BaseModel):
  name: Annotated[str, Field(min_length=1)]


class GreetingReply(BaseModel):
  message: str


GREET = RequestSchema[Greeting, GreetingReply](
  id="example.greet", input=Greeting, output=GreetingReply
)
GREETED = EventSchema[Greeting](id="example.greeted", payload=Greeting)
