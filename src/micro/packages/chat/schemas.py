"""What chat asks greeter for, and what it hands to audit's queue."""

from typing import Annotated

from pydantic import BaseModel, Field

from micro.service import RequestSchema, WorkQueue


class Greeting(BaseModel):
  name: Annotated[str, Field(min_length=1)]


class GreetingReply(BaseModel):
  message: str


GREET = RequestSchema[Greeting, GreetingReply](
  id="example.greet", input=Greeting, output=GreetingReply
)
AUDIT = WorkQueue[Greeting]("example.audit", Greeting)
