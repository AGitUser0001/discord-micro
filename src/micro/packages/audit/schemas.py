"""What audit expects to hear. These match what greeter and ticker send by id and
shape; services agree through validated messages, not shared code."""

from pydantic import BaseModel

from micro.service import EventSchema, WorkQueue


class Greeting(BaseModel):
  name: str


class Tick(BaseModel):
  count: int


GREETED = EventSchema[Greeting](id="example.greeted", payload=Greeting)
TICKED = EventSchema[Tick](id="example.ticked", payload=Tick)
AUDIT = WorkQueue[Greeting]("example.audit", Greeting)
