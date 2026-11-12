"""Answers `example.greet` and tells everyone who listens."""

from micro.discord import Context
from micro.service import Service

from .schemas import GREET, GREETED, Greeting, GreetingReply

service = Service("greeter")


@service.handle(GREET)
async def greet(ctx: Context, request: Greeting) -> GreetingReply:
  await service.client.emit(GREETED, request)
  return GreetingReply(message=f"Hello, {request.name}!")
