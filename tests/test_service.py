from typing import Any

import pytest
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.testclient import TestClient

from micro.service import (
  DuplicateEndpointError,
  DuplicateEventHandlerError,
  DuplicateRequestHandlerError,
  EventSchema,
  EventScope,
  JsonValue,
  RequestSchema,
  Service,
)

MESSAGE = EventSchema[dict[str, Any]](
  id="discord.message-create",
  scope=EventScope.guild(),
  payload={
    "type": "object",
    "properties": {
      "guild_id": {"type": "string"},
      "content": {"type": "string"},
    },
    "required": ["guild_id", "content"],
    "additionalProperties": False,
  },
)

GREETING = RequestSchema[dict[str, str], dict[str, str]](
  id="example.greeting",
  input={
    "type": "object",
    "properties": {"name": {"type": "string"}},
    "required": ["name"],
    "additionalProperties": False,
  },
  output={
    "type": "object",
    "properties": {"message": {"type": "string"}},
    "required": ["message"],
    "additionalProperties": False,
  },
)


def test_event_endpoint_invokes_handler() -> None:
  service = Service("messages")
  received: list[dict[str, Any]] = []

  @service.listen(MESSAGE)
  async def message(event: dict[str, Any]) -> None:
    received.append(event)

  with TestClient(service) as client:
    response = client.post(
      "/events/discord.message-create",
      json={"guild_id": "123", "content": "hello"},
    )

  assert response.status_code == 204
  assert received == [{"guild_id": "123", "content": "hello"}]


def test_event_payload_is_validated() -> None:
  service = Service("messages")

  @service.listen(MESSAGE)
  async def message(event: dict[str, Any]) -> None:
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
  async def first(event: dict[str, Any]) -> None:
    pass

  with pytest.raises(DuplicateEventHandlerError):

    @service.listen(MESSAGE)
    async def second(event: dict[str, Any]) -> None:
      pass


def test_duplicate_path_fails_during_declaration() -> None:
  service = Service("messages")
  custom = EventSchema[dict[str, Any]](
    id="custom.health",
    path="/health/ready",
    payload=True,
  )

  with pytest.raises(DuplicateEndpointError):

    @service.listen(custom)
    async def health(event: dict[str, Any]) -> None:
      pass


def test_schema_accounts_for_mount_path_without_changing_hash() -> None:
  service = Service("messages")

  @service.listen(MESSAGE)
  async def message(event: dict[str, Any]) -> None:
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
  async def message(event: dict[str, Any]) -> None:
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


def test_custom_decoder_supplies_typed_event() -> None:
  service = Service("numbers")

  def decode_number(value: JsonValue) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
      raise TypeError("Expected an integer.")
    return value

  number = EventSchema[int](
    id="example.number",
    payload={"type": "integer"},
    decoder=decode_number,
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
  async def message(event: dict[str, Any]) -> None:
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
  later = EventSchema[dict[str, Any]](id="example.later", payload=True)

  with TestClient(service) as client:
    assert client.get("/health/live").status_code == 204

  with pytest.raises(RuntimeError):

    @service.listen(later)
    async def handler(event: dict[str, Any]) -> None:
      pass


def test_request_handler_returns_validated_json() -> None:
  service = Service("greetings")

  @service.handle(GREETING)
  async def greet(request: dict[str, str]) -> dict[str, str]:
    return {"message": f"Hello, {request['name']}!"}

  with TestClient(service) as client:
    response = client.post("/requests/example.greeting", json={"name": "Lucas"})

  assert response.status_code == 200
  assert response.json() == {"message": "Hello, Lucas!"}


def test_request_input_and_output_are_validated() -> None:
  invalid_input_service = Service("invalid-input")

  @invalid_input_service.handle(GREETING)
  async def input_handler(request: dict[str, str]) -> dict[str, str]:
    raise AssertionError("Invalid input must not reach the handler.")

  with TestClient(invalid_input_service) as client:
    invalid_input = client.post("/requests/example.greeting", json={})

  assert invalid_input.status_code == 422

  invalid_output_service = Service("invalid-output")

  @invalid_output_service.handle(GREETING)
  async def output_handler(request: dict[str, str]) -> dict[str, str]:
    return {"wrong": "shape"}

  with TestClient(invalid_output_service) as client:
    invalid_output = client.post("/requests/example.greeting", json={"name": "Lucas"})

  assert invalid_output.status_code == 500


def test_duplicate_request_fails_during_declaration() -> None:
  service = Service("greetings")

  @service.handle(GREETING)
  async def first(request: dict[str, str]) -> dict[str, str]:
    return {"message": request["name"]}

  with pytest.raises(DuplicateRequestHandlerError):

    @service.handle(GREETING)
    async def second(request: dict[str, str]) -> dict[str, str]:
      return {"message": request["name"]}
