import asyncio
from typing import Any

import httpx2
import pytest
from pydantic import BaseModel, ConfigDict
from starlette.testclient import TestClient

from micro._microservices import MicroserviceClient
from micro.client import NoCompatibleInstanceError, ServiceClient
from micro.gateway import GatewayClient
from micro.service import EventSchema, RequestSchema, Service
from micro.store import StoreClient


class Notice(BaseModel):
  model_config = ConfigDict(extra="forbid")

  text: str


class EchoInput(BaseModel):
  value: int


class EchoOutput(BaseModel):
  echoed: bool


NOTICE = EventSchema[Notice](
  id="example.notice",
  payload=Notice,
)

ECHO = RequestSchema[EchoInput, EchoOutput](
  id="example.echo",
  input=EchoInput,
  output=EchoOutput,
)


def service_schema() -> dict[str, Any]:
  service = Service("receiver")

  @service.listen(NOTICE)
  async def notice(event: Notice) -> None:
    pass

  @service.handle(ECHO)
  async def echo(request: EchoInput) -> EchoOutput:
    return EchoOutput(echoed=bool(request.value))

  return service.dynamic_schema()


def test_client_routes_across_compatible_instances() -> None:
  calls: list[str] = []

  def respond(request: httpx2.Request) -> httpx2.Response:
    calls.append(request.url.host)
    return httpx2.Response(204)

  async def exercise() -> None:
    schema = service_schema()
    async with ServiceClient(
      [
        ("receiver-1", "http://one.internal", schema),
        ("receiver-2", "http://two.internal", schema),
      ],
      transport=httpx2.MockTransport(respond),
    ) as client:
      await client.emit(NOTICE, Notice(text="first"))
      await client.emit(NOTICE, Notice(text="second"))

  asyncio.run(exercise())
  assert calls == ["one.internal", "two.internal"]


def test_client_validates_request_response() -> None:
  def respond(request: httpx2.Request) -> httpx2.Response:
    return httpx2.Response(200, json={"echoed": True})

  async def exercise() -> None:
    async with ServiceClient(
      [("receiver", "http://receiver.internal", service_schema())],
      transport=httpx2.MockTransport(respond),
    ) as client:
      response = await client.request(ECHO, EchoInput(value=42))
      assert response == EchoOutput(echoed=True)

  asyncio.run(exercise())


def test_client_rejects_an_incompatible_schema() -> None:
  incompatible = service_schema()
  incompatible["events"][0]["payload"] = {"type": "string"}

  async def exercise() -> None:
    async with ServiceClient(
      [("receiver", "http://receiver.internal", incompatible)]
    ) as client:
      with pytest.raises(NoCompatibleInstanceError):
        await client.emit(NOTICE, Notice(text="hello"))

  asyncio.run(exercise())


def test_overseer_state_atomically_replaces_instances() -> None:
  service = Service("consumer")
  schema = service_schema()

  with TestClient(service) as test_client:
    response = test_client.post(
      "/state",
      json={
        "revision": 4,
        "instances": [
          {
            "id": "receiver-1",
            "base_url": "http://receiver.internal",
            "schema": schema,
          }
        ],
      },
    )
    stale = test_client.post(
      "/state",
      json={"revision": 3, "instances": []},
    )

  assert response.status_code == 204
  assert stale.status_code == 409
  assert service.client.state_revision == 4
  assert service.client.instance_ids == ("receiver-1",)


def test_service_owns_clients_for_every_microservice_kind() -> None:
  service = Service("consumer")
  schema = service_schema()

  with TestClient(service) as test_client:
    response = test_client.post(
      "/state",
      json={
        "revision": 2,
        "instances": [
          {
            "id": "receiver-1",
            "base_url": "http://receiver.internal",
            "schema": schema,
          }
        ],
        "stores": [
          {
            "id": "store-1",
            "base_url": "http://store.internal",
            "modules": ["example"],
          }
        ],
        "gateways": [{"id": "gateway-1", "base_url": "http://gateway.internal"}],
        "queues": [{"id": "queue-1", "base_url": "http://queue.internal"}],
      },
    )

    assert response.status_code == 204
    assert service.client.instance_ids == ("receiver-1",)
    assert service.store.instance_ids == ("store-1",)
    assert service.gateway.instance_ids == ("gateway-1",)
    assert service.queue.instance_ids == ("queue-1",)


def test_store_and_gateway_clients_share_the_microservice_client_backbone() -> None:
  assert issubclass(StoreClient, MicroserviceClient)
  assert issubclass(GatewayClient, MicroserviceClient)
