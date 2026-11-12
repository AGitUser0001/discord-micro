"""Listens to application events and records them through a durable work queue."""

from micro.discord import Context
from micro.service import Service

from .schemas import AUDIT, GREETED, TICKED, Greeting, Tick

service = Service("audit")


@service.listen(GREETED)
async def greeted(ctx: Context, event: Greeting) -> None:
  await service.client.enqueue(AUDIT, event)


@service.work(AUDIT)
async def record(ctx: Context, job: Greeting) -> None:
  print(f"audit: greeted {job.name}")


@service.listen(TICKED)
async def ticked(ctx: Context, event: Tick) -> None:
  print(f"audit: tick {event.count}")
