"""A background component: emits a tick every minute while it runs."""

import asyncio

from pydantic import BaseModel

from micro.runtime import Component
from micro.service import Client, EventSchema


class Tick(BaseModel):
  count: int


TICKED = EventSchema[Tick](id="example.ticked", payload=Tick)


class Ticker(Component):
  def __init__(self) -> None:
    super().__init__("ticker")

  async def on_start(self) -> None:
    self.spawn(self._tick(), name="tick")

  async def _tick(self) -> None:
    client = Client(self.runtime)
    count = 0
    while self.active:
      count += 1
      await client.emit(TICKED, Tick(count=count))
      await asyncio.sleep(60)


ticker = Ticker()
