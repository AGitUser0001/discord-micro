import asyncio
from collections import Counter

import pytest
from pydantic import BaseModel, ConfigDict

from micro import subjects
from micro.errors import RemoteError, RoutingError
from micro.runtime import Runtime
from micro.service import (
  DuplicateRequestHandlerError,
  EventSchema,
  RequestSchema,
  Service,
  ServiceError,
  WorkQueue,
)


class Greeting(BaseModel):
  model_config = ConfigDict(extra="forbid")
  name: str


class GreetingResponse(BaseModel):
  model_config = ConfigDict(extra="forbid")
  message: str


class Note(BaseModel):
  text: str


GREET = RequestSchema[Greeting, GreetingResponse](
  id="example.greet", input=Greeting, output=GreetingResponse
)
NOTED = EventSchema[Note](id="example.noted", payload=Note)
JOBS = WorkQueue[Note]("example.jobs", Note)


async def eventually(predicate, *, timeout: float = 10.0) -> None:
  deadline = asyncio.get_running_loop().time() + timeout
  while not predicate():
    if asyncio.get_running_loop().time() > deadline:
      raise AssertionError("condition was not met in time")
    await asyncio.sleep(0.02)


def greeter(name: str = "greeter", tag: str = "") -> Service:
  service = Service(name)

  @service.handle(GREET)
  async def greet(request: Greeting) -> GreetingResponse:
    if request.name == "nobody":
      raise ServiceError("unknown_person", "Nobody is not a person.", detail={"x": 1})
    if request.name == "crash":
      raise RuntimeError("boom")
    return GreetingResponse(message=f"Hello, {request.name}!{tag}")

  return service


def test_requests_are_typed_and_errors_carry_codes(nats_url: str) -> None:
  async def exercise() -> None:
    async with Runtime(nats_url) as runtime:
      service = greeter()
      await runtime.add(service)
      client = service.client
      reply = await client.request(GREET, Greeting(name="Ada"))
      assert reply == GreetingResponse(message="Hello, Ada!")

      with pytest.raises(RemoteError) as error:
        await client.request(GREET, Greeting(name="nobody"))
      assert (error.value.code, error.value.detail) == ("unknown_person", {"x": 1})

      with pytest.raises(RemoteError) as error:
        await client.request(GREET, Greeting(name="crash"))
      assert error.value.code == "handler_failed"

      other = RequestSchema[Note, GreetingResponse](
        id="example.greet", input=Note, output=GreetingResponse
      )
      with pytest.raises(RemoteError) as error:
        await client.request(other, Note(text="hi"))
      assert error.value.code == "incompatible_schema"

      missing = RequestSchema[Note, Note](id="example.missing", input=Note, output=Note)
      with pytest.raises(RoutingError):
        await client.request(missing, Note(text="hi"))

  asyncio.run(exercise())


def test_replicas_share_requests_and_drain_loses_nothing(nats_url: str) -> None:
  async def exercise() -> None:
    first_runtime = Runtime(nats_url)
    second_runtime = Runtime(nats_url)
    await first_runtime.add(greeter(tag="1"))
    await second_runtime.add(greeter(tag="2"))
    async with Runtime(nats_url) as caller:
      from micro.service import Client

      client = Client(caller)
      replies = await asyncio.gather(
        *(client.request(GREET, Greeting(name=str(i))) for i in range(40))
      )
      assert {reply.message[-1] for reply in replies} == {"1", "2"}

      async def load() -> list[GreetingResponse]:
        return list(
          await asyncio.gather(
            *(client.request(GREET, Greeting(name=str(i))) for i in range(200))
          )
        )

      running = asyncio.create_task(load())
      await asyncio.sleep(0)
      await first_runtime.drain()
      results = await running
      assert len(results) == 200
      await first_runtime.close()
      after = await client.request(GREET, Greeting(name="x"))
      assert after.message.endswith("2")
    await second_runtime.drain()
    await second_runtime.close()

  asyncio.run(exercise())


def test_events_reach_each_service_once_with_many_handlers(nats_url: str) -> None:
  async def exercise() -> None:
    received: Counter[str] = Counter()

    def listener(name: str) -> Service:
      service = Service(name)

      @service.listen(NOTED)
      async def first(note: Note) -> None:
        received[f"{name}:first:{note.text}"] += 1

      @service.listen(NOTED, when=lambda note: note.text.startswith("a"))
      async def second(note: Note) -> None:
        received[f"{name}:second:{note.text}"] += 1

      return service

    runtimes = [Runtime(nats_url) for _ in range(3)]
    await runtimes[0].add(listener("audit"))
    await runtimes[1].add(listener("audit"))
    await runtimes[2].add(listener("search"))
    async with Runtime(nats_url) as caller:
      from micro.service import Client

      client = Client(caller)
      for text in ("apple", "banana"):
        await client.emit(NOTED, Note(text=text))
      await eventually(lambda: sum(received.values()) == 6)
      await asyncio.sleep(0.3)
      assert received == Counter(
        {
          "audit:first:apple": 1,
          "audit:second:apple": 1,
          "audit:first:banana": 1,
          "search:first:apple": 1,
          "search:second:apple": 1,
          "search:first:banana": 1,
        }
      )
    for runtime in runtimes:
      await runtime.drain()
      await runtime.close()

  asyncio.run(exercise())


def test_failing_handler_is_isolated_and_event_redelivered(nats_url: str) -> None:
  async def exercise() -> None:
    attempts: Counter[str] = Counter()
    service = Service("flaky")

    @service.listen(NOTED)
    async def steady(note: Note) -> None:
      attempts["steady"] += 1

    @service.listen(NOTED)
    async def flaky(note: Note) -> None:
      attempts["flaky"] += 1
      if attempts["flaky"] == 1:
        raise RuntimeError("first try fails")

    async with Runtime(nats_url) as runtime:
      await runtime.add(service)
      await service.client.emit(NOTED, Note(text="x"))
      await eventually(lambda: attempts["flaky"] == 2)
      # At-least-once: the whole event is redelivered, so steady ran twice too.
      assert attempts["steady"] == 2

  asyncio.run(exercise())


def test_discord_dispatch_listeners_can_filter_by_guild(nats_url: str) -> None:
  async def exercise() -> None:
    from micro.schemas import events as discord_events

    seen: list[str] = []
    service = Service("guild-only")

    @service.listen(discord_events.TYPING_START, guild_id=42)
    async def typing(event: object) -> None:
      seen.append("42")

    async with Runtime(nats_url) as runtime:
      await runtime.add(service)
      payload = b'{"channel_id":"1","user_id":"2","timestamp":1}'
      for guild in (41, 42):
        await runtime.jetstream.publish(
          subjects.dispatch("TYPING_START", guild),
          payload,
          stream=subjects.EVENTS_STREAM,
        )
      await eventually(lambda: seen == ["42"])
      await asyncio.sleep(0.3)
      assert seen == ["42"]

  asyncio.run(exercise())


def test_work_queue_keeps_jobs_until_one_worker_takes_them(nats_url: str) -> None:
  async def exercise() -> None:
    done: list[str] = []
    async with Runtime(nats_url) as producer:
      from micro.service import Client

      client = Client(producer)
      for index in range(10):
        await client.enqueue(JOBS, Note(text=str(index)))

      workers = []
      for _ in range(2):
        worker = Service("worker")

        @worker.work(JOBS)
        async def process(job: Note) -> None:
          done.append(job.text)

        workers.append(worker)
      runtimes = [Runtime(nats_url), Runtime(nats_url)]
      for runtime, worker in zip(runtimes, workers):
        await runtime.add(worker)
      await eventually(lambda: len(done) == 10)
      await asyncio.sleep(0.3)
      assert sorted(done, key=int) == [str(index) for index in range(10)]
      for runtime in runtimes:
        await runtime.drain()
        await runtime.close()

  asyncio.run(exercise())


def test_presence_advertises_contracts_and_declaration_rules() -> None:
  service = greeter()

  @service.listen(NOTED)
  async def noted(note: Note) -> None:
    pass

  metadata = service.metadata()
  assert metadata["requests"] == {"example.greet": GREET.hash}
  assert metadata["events"] == ["example.noted"]
  with pytest.raises(DuplicateRequestHandlerError):

    @service.handle(GREET)
    async def again(request: Greeting) -> GreetingResponse:
      raise AssertionError

  with pytest.raises(TypeError):
    service.listen(NOTED)(lambda note: None)  # type: ignore[arg-type]
  with pytest.raises(ValueError):
    service.listen(NOTED, guild_id=1)
