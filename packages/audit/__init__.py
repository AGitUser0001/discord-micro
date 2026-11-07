"""Listens to application events and records them through a durable work queue."""

from micro.service import Service

from .schemas import AUDIT, GREETED, TICKED, Greeting, Tick

service = Service("audit")


@service.listen(GREETED)
async def greeted(event: Greeting) -> None:
  await service.client.enqueue(AUDIT, event)


@service.work(AUDIT)
async def record(job: Greeting) -> None:
  print(f"audit: greeted {job.name}")


@service.listen(TICKED)
async def ticked(event: Tick) -> None:
  print(f"audit: tick {event.count}")
