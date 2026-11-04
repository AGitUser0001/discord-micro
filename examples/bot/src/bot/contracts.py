"""Schemas shared between services: requests, events, and work queues."""

from typing import Annotated

from pydantic import BaseModel, Field

from micro.service import EventSchema, RequestSchema, WorkQueue


class Greeting(BaseModel):
  name: Annotated[str, Field(min_length=1)]


class GreetingReply(BaseModel):
  message: str


class Tick(BaseModel):
  count: int


GREET = RequestSchema[Greeting, GreetingReply](
  id="example.greet", input=Greeting, output=GreetingReply
)
GREETED = EventSchema[Greeting](id="example.greeted", payload=Greeting)
TICKED = EventSchema[Tick](id="example.ticked", payload=Tick)
AUDIT = WorkQueue[Greeting]("example.audit", Greeting)
