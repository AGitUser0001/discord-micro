from typing import Annotated, Any, cast

import pytest
from pydantic import BaseModel, ConfigDict, Field
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.testclient import TestClient

from micro.service import (
  DuplicateEndpointError,
  DuplicateEventHandlerError,
  DuplicateRequestHandlerError,
  EventSchema,
  EventScope,
  RequestSchema,
  Service,
)


class Message(BaseModel):
  model_config = ConfigDict(extra="forbid")

  guild_id: str
  content: str


class Greeting(BaseModel):
  model_config = ConfigDict(extra="forbid")

  name: str


class GreetingResponse(BaseModel):
  model_config = ConfigDict(extra="forbid")

  message: str


type PositiveInt = Annotated[int, Field(gt=0)]


MESSAGE = EventSchema[Message](
  id="discord.message-create",
  scope=EventScope.guild(),
  payload=Message,
)

GREETING = RequestSchema[Greeting, GreetingResponse](
  id="example.greeting",
  input=Greeting,
  output=GreetingResponse,
)


def test_event_endpoint_invokes_handler() -> None:
  service = Service("messages")
  received: list[Message] = []

  @service.listen(MESSAGE)
  async def message(event: Message) -> None:
    received.append(event)

  with TestClient(service) as client:
    response = client.post(
      "/events/discord.message-create",
      json={"guild_id": "123", "content": "hello"},
    )

  assert response.status_code == 204
  assert received == [Message(guild_id="123", content="hello")]


def test_event_payload_is_validated() -> None:
  service = Service("messages")

  @service.listen(MESSAGE)
  async def message(event: Message) -> None:
    raise AssertionError("Invalid events must not reach handlers.")

  with TestClient(service) as client:
    response = client.post(
      "/events/discord.message-create",
      json={"guild_id": "123"},
    )

  assert response.status_code == 422
  assert response.json()["detail"] == "Event payload does not match its schema."


def test_duplicate_event_fails_during_declaration() -> None:
  service = Service("messages")

  @service.listen(MESSAGE)
  async def first(event: Message) -> None:
    pass

  with pytest.raises(DuplicateEventHandlerError):

    @service.listen(MESSAGE)
    async def second(event: Message) -> None:
      pass


def test_duplicate_path_fails_during_declaration() -> None:
  service = Service("messages")
  custom = EventSchema[Any](
    id="custom.health",
    path="/health/ready",
    payload=Any,
  )

  with pytest.raises(DuplicateEndpointError):

    @service.listen(custom)
    async def health(event: Any) -> None:
      pass


def test_schema_accounts_for_mount_path_without_changing_hash() -> None:
  service = Service("messages")

  @service.listen(MESSAGE)
  async def message(event: Message) -> None:
    pass

  direct_schema = service.dynamic_schema()
  mounted = Starlette(routes=[Mount("/micro", service)])

  with TestClient(mounted) as client:
    response = client.get("/micro/schema")

  assert response.status_code == 200
  mounted_schema = response.json()
  assert mounted_schema["asgi"]["root_path"] == "/micro"
  assert mounted_schema["events"][0]["path"] == ("/micro/events/discord.message-create")
  assert mounted_schema["implementation_hash"] == direct_schema["implementation_hash"]


def test_drain_updates_health_and_rejects_events() -> None:
  service = Service("messages")

  @service.listen(MESSAGE)
  async def message(event: Message) -> None:
    pass

  service.drain()
  with TestClient(service) as client:
    assert client.get("/health/ready").status_code == 503
    assert client.get("/health/drained").status_code == 204
    response = client.post(
      "/events/discord.message-create",
      json={"guild_id": "123", "content": "hello"},
    )

  assert response.status_code == 503


def test_pydantic_adapter_supplies_typed_event() -> None:
  service = Service("numbers")
  number = EventSchema[int](
    id="example.number",
    payload=PositiveInt,
  )
  received: list[int] = []

  @service.listen(number)
  async def receive_number(event: int) -> None:
    received.append(event)

  with TestClient(service) as client:
    response = client.post("/events/example.number", json=42)

  assert response.status_code == 204
  assert received == [42]


def test_event_endpoint_requires_json_content_type() -> None:
  service = Service("messages")

  @service.listen(MESSAGE)
  async def message(event: Message) -> None:
    raise AssertionError("Non-JSON requests must not reach handlers.")

  with TestClient(service) as client:
    response = client.post(
      "/events/discord.message-create",
      content=b"not json",
      headers={"content-type": "application/octet-stream"},
    )

  assert response.status_code == 415


def test_handlers_cannot_be_added_after_start() -> None:
  service = Service("messages")
  later = EventSchema[Any](id="example.later", payload=Any)

  with TestClient(service) as client:
    assert client.get("/health/live").status_code == 204

  with pytest.raises(RuntimeError):

    @service.listen(later)
    async def handler(event: Any) -> None:
      pass


def test_request_handler_returns_validated_json() -> None:
  service = Service("greetings")

  @service.handle(GREETING)
  async def greet(request: Greeting) -> GreetingResponse:
    return GreetingResponse(message=f"Hello, {request.name}!")

  with TestClient(service) as client:
    response = client.post("/requests/example.greeting", json={"name": "World"})

  assert response.status_code == 200
  assert response.json() == {"message": "Hello, World!"}


def test_request_input_and_output_are_validated() -> None:
  invalid_input_service = Service("invalid-input")

  @invalid_input_service.handle(GREETING)
  async def input_handler(request: Greeting) -> GreetingResponse:
    raise AssertionError("Invalid input must not reach the handler.")

  with TestClient(invalid_input_service) as client:
    invalid_input = client.post("/requests/example.greeting", json={})

  assert invalid_input.status_code == 422

  invalid_output_service = Service("invalid-output")

  @invalid_output_service.handle(GREETING)
  async def output_handler(request: Greeting) -> GreetingResponse:
    return cast(Any, {"wrong": "shape"})

  with TestClient(invalid_output_service) as client:
    invalid_output = client.post("/requests/example.greeting", json={"name": "World"})

  assert invalid_output.status_code == 500


def test_duplicate_request_fails_during_declaration() -> None:
  service = Service("greetings")

  @service.handle(GREETING)
  async def first(request: Greeting) -> GreetingResponse:
    return GreetingResponse(message=request.name)

  with pytest.raises(DuplicateRequestHandlerError):

    @service.handle(GREETING)
    async def second(request: Greeting) -> GreetingResponse:
      return GreetingResponse(message=request.name)
