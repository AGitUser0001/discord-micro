import asyncio
from collections.abc import Sequence
from typing import Any, Literal, Protocol, Self
from urllib.parse import urlsplit

import httpx2
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, field_validator
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route
from starlette.types import Receive, Scope, Send

from micro.store import GraphModule
from micro.store.composer import MicroGraph, compose_graph


class DiscoveredInstance(BaseModel):
  """A routable process reported by a deployment's discovery implementation."""

  model_config = ConfigDict(extra="forbid", frozen=True)

  id: str = Field(min_length=1)
  base_url: str
  role: Literal["service", "store", "gateway"]
  service_schema: dict[str, Any] | None = Field(default=None, alias="schema")
  modules: tuple[str, ...] = ()

  @field_validator("base_url")
  @classmethod
  def _absolute_http_url(cls, value: str) -> str:
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
      raise ValueError("base_url must be an absolute HTTP(S) URL")
    if parsed.query or parsed.fragment:
      raise ValueError("base_url cannot contain a query or fragment")
    return value.rstrip("/")

  @field_validator("service_schema")
  @classmethod
  def _service_schema(
    cls, value: dict[str, Any] | None, info: Any
  ) -> dict[str, Any] | None:
    if info.data.get("role") == "service" and value is None:
      raise ValueError("service instances must include their dynamic schema")
    return value


class Discovery(Protocol):
  async def snapshot(self) -> Sequence[DiscoveredInstance]: ...


class NetworkDiscovery:
  """Mutable discovery with an ASGI control surface.

  Deployments must apply their own authentication before exposing this app outside
  a trusted control network.
  """

  def __init__(self, instances: Sequence[DiscoveredInstance] = ()) -> None:
    self._instances = {instance.id: instance for instance in instances}
    if len(self._instances) != len(instances):
      raise ValueError("Discovery instance IDs must be unique.")
    self._adapter = TypeAdapter(DiscoveredInstance)
    self._app = Starlette(
      routes=[
        Route("/instances", self._list, methods=["GET"]),
        Route("/instances", self._upsert, methods=["POST"]),
        Route("/instances/{instance_id}", self._remove, methods=["DELETE"]),
      ]
    )

  async def snapshot(self) -> Sequence[DiscoveredInstance]:
    return tuple(self._instances.values())

  def add(self, instance: DiscoveredInstance) -> None:
    self._instances[instance.id] = instance

  def remove(self, instance_id: str) -> bool:
    return self._instances.pop(instance_id, None) is not None

  async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
    await self._app(scope, receive, send)

  async def _list(self, request: Request) -> Response:
    return Response(
      TypeAdapter(tuple[DiscoveredInstance, ...]).dump_json(
        tuple(self._instances.values())
      ),
      media_type="application/json",
    )

  async def _upsert(self, request: Request) -> Response:
    if (
      request.headers.get("content-type", "").partition(";")[0].strip()
      != "application/json"
    ):
      return JSONResponse(
        {"detail": "Discovery requires application/json."}, status_code=415
      )
    try:
      instance = self._adapter.validate_json(await request.body())
    except ValueError as exc:
      return JSONResponse(
        {"detail": "Invalid discovery instance.", "message": str(exc)},
        status_code=422,
      )
    self.add(instance)
    return Response(status_code=204)

  async def _remove(self, request: Request) -> Response:
    return Response(
      status_code=204 if self.remove(request.path_params["instance_id"]) else 404
    )


class TopologyPushError(RuntimeError):
  def __init__(self, failures: Sequence[tuple[str, int, str]]) -> None:
    self.failures = tuple(failures)
    names = ", ".join(instance_id for instance_id, _, _ in failures)
    super().__init__(f"Topology was rejected by: {names}")


class Overseer:
  """Builds topology from injected discovery and pushes it to every instance."""

  def __init__(
    self,
    discovery: Discovery,
    *,
    transport: httpx2.AsyncBaseTransport | None = None,
    timeout: float = 5.0,
    modules: Sequence[GraphModule] = (),
  ) -> None:
    self.discovery = discovery
    self._revision = -1
    self._instances: tuple[DiscoveredInstance, ...] = ()
    self._modules = {module.id: module for module in modules}
    if len(self._modules) != len(modules):
      raise ValueError("Store module IDs must be unique.")
    self._store_graphs: dict[str, MicroGraph] = {}
    self._http = httpx2.AsyncClient(transport=transport, timeout=timeout)
    self._app = Starlette(
      routes=[
        Route("/health/live", self._live, methods=["GET"]),
        Route("/topology", self._topology, methods=["GET"]),
        Route("/refresh", self._refresh, methods=["POST"]),
      ]
    )

  async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
    if scope["type"] != "lifespan":
      await self._app(scope, receive, send)
      return
    await self._lifespan(receive, send)

  async def reconcile(self) -> int:
    instances = tuple(await self.discovery.snapshot())
    ids = [instance.id for instance in instances]
    if len(ids) != len(set(ids)):
      raise ValueError("Discovery returned duplicate instance IDs.")
    revision = self._revision + 1
    service_state = {
      "revision": revision,
      "instances": [
        {
          "id": instance.id,
          "base_url": instance.base_url,
          "schema": instance.service_schema,
        }
        for instance in instances
        if instance.role == "service"
      ],
      "stores": [
        {
          "id": instance.id,
          "base_url": instance.base_url,
          "modules": list(instance.modules),
        }
        for instance in instances
        if instance.role == "store"
      ],
      "gateways": [
        {
          "id": instance.id,
          "base_url": instance.base_url,
        }
        for instance in instances
        if instance.role == "gateway"
      ],
    }
    store_modules: dict[str, tuple[GraphModule, ...]] = {}
    for instance in instances:
      if instance.role != "store":
        continue
      try:
        store_modules[instance.id] = tuple(
          self._modules[module_id] for module_id in instance.modules
        )
      except KeyError as exc:
        raise ValueError(
          f"Store {instance.id!r} requests unknown module {exc.args[0]!r}."
        ) from exc
    composed_by_assignment: dict[tuple[str, ...], MicroGraph] = {}
    store_graphs: dict[str, MicroGraph] = {}
    for instance_id, modules in store_modules.items():
      if not modules:
        continue
      assignment = tuple(module.id for module in modules)
      graph = composed_by_assignment.get(assignment)
      if graph is None:
        graph = compose_graph(modules)
        composed_by_assignment[assignment] = graph
      store_graphs[instance_id] = graph

    async def push(instance: DiscoveredInstance) -> tuple[str, int, str] | None:
      if instance.role == "service":
        endpoint = "/state"
        body: Any = service_state
      elif instance.role == "store":
        endpoint = "/topology"
        body = {
          "revision": revision,
          "modules": [
            module.model_dump(mode="json", by_alias=True)
            for module in store_modules[instance.id]
          ],
        }
      else:
        return None
      response = await self._http.post(f"{instance.base_url}{endpoint}", json=body)
      if response.is_success:
        return None
      return instance.id, response.status_code, response.text

    results = await asyncio.gather(*(push(instance) for instance in instances))
    failures = tuple(result for result in results if result is not None)
    if failures:
      raise TopologyPushError(failures)
    self._instances = instances
    self._store_graphs = store_graphs
    self._revision = revision
    return revision

  async def aclose(self) -> None:
    await self._http.aclose()

  @property
  def revision(self) -> int:
    return self._revision

  @property
  def graph_modules(self) -> tuple[GraphModule, ...]:
    return tuple(self._modules.values())

  @property
  def store_graphs(self) -> dict[str, MicroGraph]:
    return dict(self._store_graphs)

  def load_graphql_module(self, module: GraphModule) -> None:
    self._modules[module.id] = module

  def unload_graphql_module(self, module_id: str) -> bool:
    if module_id not in self._modules:
      return False
    del self._modules[module_id]
    return True

  async def __aenter__(self) -> Self:
    return self

  async def __aexit__(self, *exc_info: object) -> None:
    await self.aclose()

  async def _live(self, request: Request) -> Response:
    return Response(status_code=204)

  async def _topology(self, request: Request) -> Response:
    return JSONResponse(
      {
        "revision": self._revision,
        "instances": [
          instance.model_dump(mode="json", by_alias=True)
          for instance in self._instances
        ],
      }
    )

  async def _refresh(self, request: Request) -> Response:
    try:
      revision = await self.reconcile()
    except (TypeError, ValueError, httpx2.HTTPError, TopologyPushError) as exc:
      return JSONResponse(
        {"detail": "Topology reconciliation failed.", "message": str(exc)},
        status_code=503,
      )
    return JSONResponse({"revision": revision})

  async def _lifespan(self, receive: Receive, send: Send) -> None:
    while True:
      message = await receive()
      if message["type"] == "lifespan.startup":
        await send({"type": "lifespan.startup.complete"})
      elif message["type"] == "lifespan.shutdown":
        await self.aclose()
        await send({"type": "lifespan.shutdown.complete"})
        return
