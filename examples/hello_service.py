from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from micro.service import EventSchema, EventScope, RequestSchema, Service

service = Service("hello")


class GreetingPayload(BaseModel):
  model_config = ConfigDict(extra="forbid")

  name: Annotated[str, Field(min_length=1)]


class GreetingResponse(BaseModel):
  message: str


Greeting = EventSchema[GreetingPayload](
  id="example.greeting",
  scope=EventScope.keyed("name"),
  payload=GreetingPayload,
)

GreetingRequest = RequestSchema[GreetingPayload, GreetingResponse](
  id="example.get-greeting",
  input=GreetingPayload,
  output=GreetingResponse,
)


@service.listen(Greeting)
async def greet(event: GreetingPayload) -> None:
  print(f"Hello, {event.name}!")


@service.handle(GreetingRequest)
async def get_greeting(request: GreetingPayload) -> GreetingResponse:
  return GreetingResponse(message=f"Hello, {request.name}!")
