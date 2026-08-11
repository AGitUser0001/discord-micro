import asyncio
import hashlib
import json
from collections.abc import AsyncIterator, Awaitable, Callable, Sequence
from contextlib import asynccontextmanager
from typing import Any, Literal, Protocol, Self
from urllib.parse import urlsplit

import httpx2
from pydantic import (
  BaseModel,
  ConfigDict,
  Field,
  JsonValue,
  TypeAdapter,
  field_validator,
  model_validator,
)
from pydantic_core import to_json
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route
from starlette.types import Receive, Scope, Send

from micro._microservices import DiscordCredential, TopologyError, request_content_type
from micro.gateway import (
  ConnectionEvent,
  ConnectionEventKind,
  GatewayState,
  ShardAssignment,
)
from micro.store import GraphModule
from micro.store.composer import (
  DirectiveMetadata,
  MicroGraph,
  TypeDirectiveMetadata,
  compose_graph,
)


class DiscoveredInstance(BaseModel):
  """A routable process reported by a deployment's discovery implementation."""

  model_config = ConfigDict(extra="forbid", frozen=True)

  id: str = Field(min_length=1)
  base_url: str
  role: Literal[
    "service",
    "store",
    "gateway",
    "gateway.event_service",
    "gateway.projection",
    "discord.http",
    "queue",
  ]
  service_schema: dict[str, Any] | None = Field(default=None, alias="schema")
  modules: tuple[str, ...] = ()
  shard_ids: tuple[int, ...] = ()
  shard_count: int | None = Field(default=None, ge=1, le=4096)

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
    if info.data.get("role") == "service":
      if value is None:
        raise ValueError("service instances must include their dynamic schema")
      if not isinstance(value.get("service"), str) or not value["service"]:
        raise ValueError("service schemas must include a non-empty service name")
    return value

  @model_validator(mode="after")
  def _gateway_shards(self) -> DiscoveredInstance:
    if self.role != "gateway":
      if self.shard_ids or self.shard_count is not None:
        raise ValueError("only gateway instances may declare shard ownership")
      return self
    if self.shard_ids and self.shard_count is None:
      raise ValueError("gateway shard_count is required with shard_ids")
    if self.shard_count is not None and any(
      shard_id < 0 or shard_id >= self.shard_count for shard_id in self.shard_ids
    ):
      raise ValueError("gateway shard IDs must be within shard_count")
    if len(set(self.shard_ids)) != len(self.shard_ids):
      raise ValueError("gateway shard IDs must be unique")
    return self


class DiscoverySnapshot(BaseModel):
  model_config = ConfigDict(extra="forbid", frozen=True)

  instances: tuple[DiscoveredInstance, ...] = ()
  discord_credential: DiscordCredential | None = None


class Discovery(Protocol):
  async def snapshot(self) -> DiscoverySnapshot: ...


class OverseerPersistence(Protocol):
  async def load(self) -> dict[str, JsonValue] | None: ...
  async def save(self, state: dict[str, JsonValue]) -> None: ...


class MemoryOverseerPersistence:
  def __init__(self) -> None:
    self.state: dict[str, JsonValue] | None = None

  async def load(self) -> dict[str, JsonValue] | None:
    return dict(self.state) if self.state is not None else None

  async def save(self, state: dict[str, JsonValue]) -> None:
    self.state = dict(state)


class ReconciliationResult(BaseModel):
  model_config = ConfigDict(extra="forbid", frozen=True)
  revision: int
  desired_instances: tuple[str, ...]
  distributed_instances: tuple[str, ...]
  failures: tuple[tuple[str, int, str], ...] = ()


class NetworkDiscovery:
  """Mutable discovery with an ASGI control surface.

  Deployments must apply their own authentication before exposing this app outside
  a trusted control network.
  """

  def __init__(
    self,
    instances: Sequence[DiscoveredInstance] = (),
    *,
    discord_credential: DiscordCredential | None = None,
  ) -> None:
    self._instances = {instance.id: instance for instance in instances}
    if len(self._instances) != len(instances):
      raise ValueError("Discovery instance IDs must be unique.")
    self._discord_credential = discord_credential
    self._app = Starlette(
      routes=[
        Route("/instances", self._list, methods=["GET"]),
        Route("/instances", self._upsert, methods=["POST"]),
        Route("/instances/{instance_id}", self._remove, methods=["DELETE"]),
        Route("/discord/credential", self._credential_status, methods=["GET"]),
        Route("/discord/credential", self._set_credential, methods=["POST"]),
        Route("/discord/credential", self._clear_credential, methods=["DELETE"]),
      ]
    )

  async def snapshot(self) -> DiscoverySnapshot:
    return DiscoverySnapshot(
      instances=tuple(self._instances.values()),
      discord_credential=self._discord_credential,
    )

  def add(self, instance: DiscoveredInstance) -> None:
    self._instances[instance.id] = instance

  def remove(self, instance_id: str) -> bool:
    return self._instances.pop(instance_id, None) is not None

  def set_discord_credential(self, credential: DiscordCredential) -> None:
    current = self._discord_credential
    if current is not None:
      if credential.revision < current.revision:
        raise ValueError("Discord credential revision is stale.")
      if credential.revision == current.revision and credential.token != current.token:
        raise ValueError("A revision cannot identify two Discord credentials.")
    self._discord_credential = credential

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
    if request_content_type(request) != "application/json":
      return JSONResponse(
        {"detail": "Discovery requires application/json."}, status_code=415
      )
    try:
      instance = DiscoveredInstance.model_validate_json(await request.body())
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

  async def _credential_status(self, request: Request) -> Response:
    credential = self._discord_credential
    return JSONResponse(
      {
        "configured": credential is not None,
        "revision": credential.revision if credential is not None else None,
      }
    )

  async def _set_credential(self, request: Request) -> Response:
    if request_content_type(request) != "application/json":
      return JSONResponse(
        {"detail": "Credential updates require application/json."},
        status_code=415,
      )
    try:
      credential = DiscordCredential.model_validate_json(await request.body())
      self.set_discord_credential(credential)
    except ValueError as exc:
      return JSONResponse(
        {"detail": "Invalid Discord credential.", "message": str(exc)},
        status_code=422,
      )
    return Response(status_code=204)

  async def _clear_credential(self, request: Request) -> Response:
    self._discord_credential = None
    return Response(status_code=204)


class TopologyPushError(TopologyError):
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
    directives: Sequence[DirectiveMetadata] = (),
    type_directives: Sequence[TypeDirectiveMetadata] = (),
    persistence: OverseerPersistence | None = None,
    reconcile_interval: float | None = None,
    is_active: Callable[[], bool] = lambda: True,
    max_push_concurrency: int = 100,
  ) -> None:
    self.discovery = discovery
    self._revision = -1
    self._next_revision = 0
    self._reconcile_lock = asyncio.Lock()
    self._instances: tuple[DiscoveredInstance, ...] = ()
    self._desired_instances: tuple[DiscoveredInstance, ...] = ()
    self._distributed: dict[str, int] = {}
    self._last_result: ReconciliationResult | None = None
    self._persistence = persistence
    self._restored = False
    self._persisted_connections: list[dict[str, JsonValue]] = []
    if reconcile_interval is not None and not 0.1 <= reconcile_interval <= 86400:
      raise ValueError("reconcile_interval must be 0.1 through 86400 seconds.")
    self._reconcile_interval = reconcile_interval
    self._reconciler: asyncio.Task[None] | None = None
    self._periodic_error: str | None = None
    self._is_active = is_active
    if max_push_concurrency <= 0:
      raise ValueError("max_push_concurrency must be positive.")
    self._push_concurrency = asyncio.Semaphore(max_push_concurrency)
    self._modules = {module.id: module for module in modules}
    if len(self._modules) != len(modules):
      raise ValueError("Store module IDs must be unique.")
    self._store_graphs: dict[str, MicroGraph] = {}
    self._gateway_state = GatewayState()
    self._directives = tuple(directives)
    self._type_directives = tuple(type_directives)
    self._http = httpx2.AsyncClient(transport=transport, timeout=timeout)
    self._app = Starlette(
      lifespan=self._lifespan,
      routes=[
        Route("/health/live", self._live, methods=["GET"]),
        Route("/topology", self._topology, methods=["GET"]),
        Route("/refresh", self._refresh, methods=["POST"]),
      ],
    )

  async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
    await self._app(scope, receive, send)

  async def reconcile(self) -> int:
    async with self._reconcile_lock:
      await self._restore()
      return await self._reconcile()

  async def _reconcile(self) -> int:
    if not self._is_active():
      raise RuntimeError(
        "This overseer is not the externally selected active instance."
      )
    snapshot = await self.discovery.snapshot()
    instances = snapshot.instances
    credential = snapshot.discord_credential
    self._desired_instances = instances
    ids = [instance.id for instance in instances]
    if len(ids) != len(set(ids)):
      raise ValueError("Discovery returned duplicate instance IDs.")
    revision = self._next_revision
    self._next_revision += 1
    await self._persist()
    schemas: dict[str, dict[str, Any]] = {}
    self._gateway_state.set_desired(
      tuple(
        ShardAssignment(instance.id, shard_id, instance.shard_count)
        for instance in instances
        if instance.role == "gateway" and instance.shard_count is not None
        for shard_id in instance.shard_ids
      )
    )
    if self._persisted_connections:
      for connection in self._persisted_connections:
        try:
          instance_id = connection["instance_id"]
          event = connection["event"]
          shard_id = connection["shard_id"]
          if (
            not isinstance(instance_id, str)
            or not isinstance(event, str)
            or isinstance(shard_id, bool)
            or not isinstance(shard_id, int)
          ):
            continue
          self._gateway_state.observe(
            instance_id,
            ConnectionEvent(
              ConnectionEventKind(event),
              shard_id,
              (
                str(connection["connection_id"])
                if connection.get("connection_id") is not None
                else None
              ),
            ),
          )
        except KeyError, TypeError, ValueError:
          continue
      self._persisted_connections.clear()
    service_instances: list[dict[str, str]] = []
    for instance in instances:
      if instance.role != "service":
        continue
      assert instance.service_schema is not None
      encoded_schema = json.dumps(
        instance.service_schema,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
      ).encode()
      schema_hash = f"sha256:{hashlib.sha256(encoded_schema).hexdigest()}"
      schemas.setdefault(schema_hash, instance.service_schema)
      service_instances.append(
        {
          "id": instance.id,
          "base_url": instance.base_url,
          "schema": schema_hash,
        }
      )

    service_state = {
      "revision": revision,
      "schemas": schemas,
      "instances": service_instances,
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
          "shard_ids": list(instance.shard_ids),
          "active_shard_ids": list(self._gateway_state.active_shards(instance.id)),
          "shard_count": instance.shard_count,
        }
        for instance in instances
        if instance.role == "gateway"
      ],
      "queues": [
        {
          "id": instance.id,
          "base_url": instance.base_url,
        }
        for instance in instances
        if instance.role == "queue"
      ],
    }
    service_state_body = to_json(service_state)
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
    store_topology_bodies: dict[tuple[str, ...], bytes] = {}
    store_graphs: dict[str, MicroGraph] = {}
    for instance_id, modules in store_modules.items():
      if not modules:
        continue
      assignment = tuple(module.id for module in modules)
      graph = composed_by_assignment.get(assignment)
      if graph is None:
        graph = compose_graph(
          modules,
          directives=self._directives,
          type_directives=self._type_directives,
        )
        composed_by_assignment[assignment] = graph
      store_graphs[instance_id] = graph
    for instance_id, modules in store_modules.items():
      assignment = tuple(module.id for module in modules)
      store_topology_bodies.setdefault(
        assignment,
        to_json(
          {
            "revision": revision,
            "modules": [
              module.model_dump(mode="json", by_alias=True) for module in modules
            ],
          }
        ),
      )

    async def post(
      instance: DiscoveredInstance, endpoint: str, body: bytes
    ) -> tuple[str, int, str] | None:
      async with self._push_concurrency:
        response = await self._http.post(
          f"{instance.base_url}{endpoint}",
          content=body,
          headers={"content-type": "application/json"},
        )
      if response.is_success:
        return None
      return instance.id, response.status_code, response.text

    async def push(instance: DiscoveredInstance) -> tuple[str, int, str] | None:
      if instance.role in {
        "service",
        "gateway",
        "gateway.event_service",
        "gateway.projection",
        "discord.http",
      }:
        endpoint = "/state"
        body = service_state_body
      elif instance.role == "store":
        endpoint = "/topology"
        assignment = tuple(module.id for module in store_modules[instance.id])
        body = store_topology_bodies[assignment]
      else:
        return None
      failure = await post(instance, endpoint, body)
      if failure is not None:
        return failure
      if instance.role in {"gateway", "discord.http"}:
        if credential is None:
          return instance.id, 503, "Discord credential is not configured."
        return await post(instance, "/discord/credential", credential.wire_bytes())
      return None

    results = await asyncio.gather(*(push(instance) for instance in instances))
    failures = tuple(result for result in results if result is not None)
    failed_ids = {item[0] for item in failures}
    distributed = tuple(
      instance.id
      for instance in instances
      if instance.role == "queue" or instance.id not in failed_ids
    )
    for instance_id in distributed:
      self._distributed[instance_id] = revision
    self._last_result = ReconciliationResult(
      revision=revision,
      desired_instances=tuple(instance.id for instance in instances),
      distributed_instances=distributed,
      failures=failures,
    )
    await self._persist()
    if failures:
      raise TopologyPushError(failures)
    self._instances = instances
    self._store_graphs = store_graphs
    self._revision = revision
    return revision

  async def aclose(self) -> None:
    if self._reconciler is not None:
      self._reconciler.cancel()
      await asyncio.gather(self._reconciler, return_exceptions=True)
      self._reconciler = None
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

  def load_graph_module(self, module: GraphModule) -> None:
    self._modules[module.id] = module

  def unload_graph_module(self, module_id: str) -> bool:
    if module_id not in self._modules:
      return False
    del self._modules[module_id]
    return True

  def observe_gateway_connection(
    self, instance_id: str, event: ConnectionEvent
  ) -> None:
    """Record a worker report without changing its desired assignment."""
    self._gateway_state.observe(instance_id, event)

  def gateway_connection_sink(
    self, instance_id: str
  ) -> Callable[[ConnectionEvent], Awaitable[None]]:
    async def observe(event: ConnectionEvent) -> None:
      self.observe_gateway_connection(instance_id, event)

    return observe

  async def declare_gateway_dead(self, instance_id: str) -> tuple[str, ...]:
    """Abandon a dead worker and purge every connection-owned projection."""
    connection_ids = self._gateway_state.declare_dead(instance_id)
    failures: list[tuple[str, int, str]] = []
    for projection in self._instances:
      if projection.role != "gateway.projection":
        continue
      for connection_id in connection_ids:
        response = await self._http.delete(
          f"{projection.base_url}/projection/connections/{connection_id}"
        )
        if not response.is_success:
          failures.append((projection.id, response.status_code, response.text))
    if failures:
      raise TopologyPushError(failures)
    return connection_ids

  @property
  def gateway_state(self) -> GatewayState:
    return self._gateway_state

  @property
  def desired_instances(self) -> tuple[DiscoveredInstance, ...]:
    return self._desired_instances

  @property
  def distributed_revisions(self) -> dict[str, int]:
    return dict(self._distributed)

  @property
  def last_reconciliation(self) -> ReconciliationResult | None:
    return self._last_result

  async def _restore(self) -> None:
    if self._restored:
      return
    self._restored = True
    if self._persistence is None:
      return
    state = await self._persistence.load()
    if state is None:
      return
    next_revision = state.get("next_revision")
    distributed = state.get("distributed")
    if isinstance(next_revision, int) and not isinstance(next_revision, bool):
      self._next_revision = max(self._next_revision, next_revision)
    if isinstance(distributed, dict):
      self._distributed = {
        key: value
        for key, value in distributed.items()
        if isinstance(key, str)
        and isinstance(value, int)
        and not isinstance(value, bool)
      }
    connections = state.get("observed_connections")
    if isinstance(connections, list):
      self._persisted_connections = [
        item for item in connections if isinstance(item, dict)
      ]

  async def _persist(self) -> None:
    if self._persistence is not None:
      await self._persistence.save(
        {
          "next_revision": self._next_revision,
          "distributed": dict(self._distributed),
          "observed_connections": [
            {
              "instance_id": connection.instance_id,
              "shard_id": connection.shard_id,
              "connection_id": connection.connection_id,
              "event": connection.event.value,
              "active": connection.active,
              "terminal": connection.terminal,
            }
            for connection in self._gateway_state.connections
          ],
        }
      )

  async def _periodic_reconcile(self) -> None:
    assert self._reconcile_interval is not None
    while True:
      await asyncio.sleep(self._reconcile_interval)
      try:
        await self.reconcile()
      except Exception as exc:
        self._periodic_error = str(exc)
      else:
        self._periodic_error = None

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
        "desired_instances": [
          instance.model_dump(mode="json", by_alias=True)
          for instance in self._desired_instances
        ],
        "distributed_instances": [
          instance.model_dump(mode="json", by_alias=True)
          for instance in self._instances
        ],
        "distributed_revisions": self._distributed,
        "observed_connections": [
          {
            "instance_id": item.instance_id,
            "shard_id": item.shard_id,
            "connection_id": item.connection_id,
            "event": item.event,
            "active": item.active,
          }
          for item in self._gateway_state.connections
        ],
        "last_reconciliation": (
          self._last_result.model_dump(mode="json")
          if self._last_result is not None
          else None
        ),
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

  @asynccontextmanager
  async def _lifespan(self, app: Starlette) -> AsyncIterator[None]:
    await self._restore()
    if self._reconcile_interval is not None:
      self._reconciler = asyncio.create_task(
        self._periodic_reconcile(), name="micro.overseer.reconcile"
      )
    try:
      yield
    finally:
      await self.aclose()
