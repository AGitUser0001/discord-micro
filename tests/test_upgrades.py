"""Rolling-upgrade behavior: old and new versions running side by side."""

import asyncio
from collections import Counter
from typing import Any

import httpx2
import pytest
from pydantic import BaseModel
from test_gateway import eventually
from test_interactions import FakeDiscord
from test_store import Executor

from micro.discord import DiscordHTTPWorker
from micro.discord.interactions import Commands, CommandSync, Interaction
from micro.errors import RemoteError
from micro.gateway import ShardLease
from micro.runtime import Registration, Runtime
from micro.service import Client, EventSchema, RequestSchema, Service
from micro.store import GraphModule, Store


def commands_service(description: str) -> Service:
  service = Service("helpdesk")
  commands = Commands(service)

  @commands.slash("help", description=description)
  async def help_(ctx: Interaction) -> None: ...

  return service


def test_commands_sync_only_when_a_rollout_converges(nats_url: str) -> None:
  discord = FakeDiscord()

  def puts() -> list[Any]:
    return [body for method, path, body in discord.calls if method == "PUT"]

  async def exercise() -> None:
    base = Runtime(nats_url)
    syncer = CommandSync()
    await base.add(
      DiscordHTTPWorker(
        "t", transport=httpx2.MockTransport(discord), api_url="https://d.test"
      ),
      syncer,
    )
    v1 = [Runtime(nats_url), Runtime(nats_url)]
    for runtime in v1:
      await runtime.add(commands_service("v1"))
    await eventually(lambda: len(puts()) == 1)
    assert puts()[-1][0]["description"] == "v1"

    # Rollout starts: v2 joins while v1 still serves. Discord keeps v1.
    v2 = [Runtime(nats_url)]
    await v2[0].add(commands_service("v2"))
    await asyncio.sleep(1.0)
    assert len(puts()) == 1

    # Rollback: v2 leaves. Nothing changed, nothing synced.
    await v2[0].drain()
    await v2[0].close()
    await asyncio.sleep(1.0)
    assert len(puts()) == 1

    # Real rollout: v2 replaces every v1 replica; only then does Discord get v2.
    v2 = [Runtime(nats_url), Runtime(nats_url)]
    for runtime in v2:
      await runtime.add(commands_service("v2"))
    await v1[0].drain()
    await v1[0].close()
    await asyncio.sleep(1.0)
    assert len(puts()) == 1
    await v1[1].drain()
    await v1[1].close()
    await eventually(lambda: len(puts()) == 2)
    assert puts()[-1][0]["description"] == "v2"

    # Every replica stopping (a restart) never unregisters the command.
    for runtime in v2:
      await runtime.drain()
      await runtime.close()
    await asyncio.sleep(1.0)
    assert len(puts()) == 2
    await base.drain()
    await base.close()

  asyncio.run(exercise())


class GreetingV1(BaseModel):
  name: str


class GreetingV2(BaseModel):
  name: str
  polite: bool = False


class GreetingV3(BaseModel):
  name: str
  language: str


def greeter(model: type[BaseModel]) -> tuple[Service, RequestSchema[Any, str]]:
  schema = RequestSchema[Any, str](id="greet", input=model, output=str)
  service = Service("greeter")

  @service.handle(schema)
  async def greet(request: Any) -> str:
    return f"hi {request.name}"

  return service, schema


def test_requests_stay_compatible_across_additive_changes(nats_url: str) -> None:
  async def exercise() -> None:
    async with Runtime(nats_url) as runtime:
      service, _ = greeter(GreetingV2)
      await runtime.add(service)
      client = Client(runtime)
      v1 = RequestSchema[GreetingV1, str](id="greet", input=GreetingV1, output=str)
      assert await client.request(v1, GreetingV1(name="old")) == "hi old"
      v3 = RequestSchema[GreetingV3, str](id="greet", input=GreetingV3, output=str)
      assert await client.request(v3, GreetingV3(name="x", language="fr")) == "hi x"
      with pytest.raises(RemoteError) as error:
        await client.request(
          RequestSchema[dict, str](id="greet", input=dict, output=str), {}
        )
      assert error.value.code == "incompatible_schema"

  asyncio.run(exercise())


class NoteV1(BaseModel):
  text: str


class NoteV2(BaseModel):
  text: str
  count: int


def listener(model: type[BaseModel], seen: Counter[str], tag: str) -> Service:
  service = Service("notes")

  @service.listen(EventSchema[Any](id="noted", payload=model))
  async def noted(note: Any) -> None:
    seen[tag] += 1

  return service


def test_events_wait_for_a_replica_that_understands_them(nats_url: str) -> None:
  async def exercise() -> None:
    seen: Counter[str] = Counter()
    old, new = Runtime(nats_url), Runtime(nats_url)
    await old.add(listener(NoteV1, seen, "v1"))
    await new.add(listener(NoteV2, seen, "v2"))
    await old.directory.wait_for(
      lambda d: len([e for e in d.entries("service") if e.name == "notes"]) == 2
    )
    client = Client(old)
    v1 = EventSchema[NoteV1](id="noted", payload=NoteV1)
    for index in range(5):
      await client.emit(v1, NoteV1(text=str(index)))
    # v2 requires `count` and cannot decode v1 events; while versions are mixed
    # they are left for v1, so none are lost.
    await eventually(lambda: seen["v1"] == 5, timeout=30)
    assert seen["v2"] == 0

    # Once every replica runs v2, an undecodable event is rejected, not retried forever.
    await old.drain()
    await old.close()
    await new.directory.wait_for(
      lambda d: len([e for e in d.entries("service") if e.name == "notes"]) == 1
    )
    await Client(new).emit(v1, NoteV1(text="orphan"))
    await asyncio.sleep(1.5)
    info = await new.jetstream.consumer_info("MICRO_EVENTS", "svc_notes")
    assert info.num_ack_pending == 0 and info.num_pending == 0
    await new.drain()
    await new.close()

  asyncio.run(exercise())


def module(version: str) -> GraphModule:
  return GraphModule(
    id="people",
    schema=f"""
      type Person @entity(key: ["name"]) {{ name: String! }}
      type Query {{
        person(name: String!): Person @from(key: {{name: name}})
        {version}(name: String!): Person @from(key: {{name: name}})
      }}
    """,
  )


def people(version: str) -> Service:
  service = Service("people")
  service.uses(module(version))
  return service


def fields(store: Store) -> set[str]:
  return set(store.engine.schema.query_type.fields)  # type: ignore[union-attr]


def test_store_modules_converge_and_survive_restarts(nats_url: str) -> None:
  async def exercise() -> None:
    base = Runtime(nats_url)
    store = Store(Executor())
    await base.add(store)
    v1 = Runtime(nats_url)
    await v1.add(people("v1"))
    await eventually(lambda: "v1" in fields(store))

    v2 = Runtime(nats_url)
    await v2.add(people("v2"))
    await asyncio.sleep(1.0)
    assert "v1" in fields(store) and "v2" not in fields(store)  # Mixed: v1 stands.

    await v1.drain()
    await v1.close()
    await eventually(lambda: "v2" in fields(store))  # Converged on v2.

    await v2.drain()
    await v2.close()
    await asyncio.sleep(1.0)
    assert "v2" in fields(store)  # Every replica gone: the module is retained.
    await base.drain()
    await base.close()

  asyncio.run(exercise())


def test_records_from_newer_versions_still_parse() -> None:
  lease = ShardLease.model_validate({"owner": "w", "ready": True, "added_later": 1})
  assert lease.owner == "w"
  entry = Registration.model_validate(
    {"kind": "service", "name": "n", "instance": "i", "id": "x", "zone": "eu"}
  )
  assert entry.name == "n"
