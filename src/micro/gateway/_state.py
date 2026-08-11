from dataclasses import dataclass, replace
from enum import StrEnum

from ._events import ConnectionEvent, ConnectionEventKind


class AssignmentState(StrEnum):
  STARTING = "starting"
  ACTIVE = "active"
  DRAINING = "draining"
  ABANDONED = "abandoned"


@dataclass(frozen=True, slots=True)
class ShardAssignment:
  instance_id: str
  shard_id: int
  shard_count: int
  state: AssignmentState = AssignmentState.STARTING


@dataclass(frozen=True, slots=True)
class ObservedConnection:
  instance_id: str
  shard_id: int
  connection_id: str | None
  event: ConnectionEventKind
  active: bool
  terminal: bool


class GatewayState:
  """Desired shard ownership and observed Discord sessions kept separately."""

  def __init__(self) -> None:
    self._assignments: dict[tuple[str, int], ShardAssignment] = {}
    self._connections: dict[tuple[str, int], ObservedConnection] = {}

  @property
  def assignments(self) -> tuple[ShardAssignment, ...]:
    return tuple(self._assignments.values())

  @property
  def connections(self) -> tuple[ObservedConnection, ...]:
    return tuple(self._connections.values())

  def set_desired(self, assignments: tuple[ShardAssignment, ...]) -> None:
    desired = {(item.instance_id, item.shard_id): item for item in assignments}
    if len(desired) != len(assignments):
      raise ValueError("Gateway assignments must be unique per instance and shard.")
    previous = self._assignments
    next_assignments: dict[tuple[str, int], ShardAssignment] = {}
    for key, item in desired.items():
      old = previous.get(key)
      next_assignments[key] = replace(item, state=old.state) if old else item
    for key, item in previous.items():
      if key not in desired and item.state is not AssignmentState.ABANDONED:
        next_assignments[key] = replace(item, state=AssignmentState.DRAINING)
    self._assignments = next_assignments

  def observe(self, instance_id: str, event: ConnectionEvent) -> ObservedConnection:
    key = (instance_id, event.shard_id)
    assignment = self._assignments.get(key)
    if assignment is None:
      raise ValueError("Connection event does not belong to a desired assignment.")
    previous = self._connections.get(key)
    connection_id = event.connection_id or (
      previous.connection_id if previous is not None else None
    )
    if event.kind in {ConnectionEventKind.READY, ConnectionEventKind.RESUMED}:
      if connection_id is None:
        raise ValueError(f"{event.kind.value} requires a connection ID.")
      if assignment.state in {AssignmentState.DRAINING, AssignmentState.ABANDONED}:
        raise ValueError("A draining or abandoned assignment cannot become active.")
      active, terminal = True, False
      competing = [
        item
        for item in self._assignments.values()
        if item.instance_id != instance_id
        and item.shard_id == event.shard_id
        and item.shard_count == assignment.shard_count
        and item.state is AssignmentState.ACTIVE
      ]
      if competing:
        raise ValueError("A shard already has an active Gateway assignment.")
      self._assignments[key] = replace(assignment, state=AssignmentState.ACTIVE)
      for competing_key, competing_assignment in tuple(self._assignments.items()):
        if (
          competing_key != key
          and competing_assignment.shard_id == event.shard_id
          and competing_assignment.shard_count == assignment.shard_count
          and competing_assignment.state is AssignmentState.DRAINING
        ):
          self._assignments[competing_key] = replace(
            competing_assignment, state=AssignmentState.ABANDONED
          )
          competing_connection = self._connections.get(competing_key)
          if competing_connection is not None:
            self._connections[competing_key] = replace(
              competing_connection, active=False
            )
      active_generation = {
        item.shard_id
        for item in self._assignments.values()
        if item.shard_count == assignment.shard_count
        and item.state is AssignmentState.ACTIVE
      }
      if active_generation == set(range(assignment.shard_count)):
        for old_key, old_assignment in tuple(self._assignments.items()):
          if (
            old_assignment.shard_count != assignment.shard_count
            and old_assignment.state is AssignmentState.DRAINING
          ):
            self._assignments[old_key] = replace(
              old_assignment, state=AssignmentState.ABANDONED
            )
            old_connection = self._connections.get(old_key)
            if old_connection is not None:
              self._connections[old_key] = replace(old_connection, active=False)
    elif event.kind is ConnectionEventKind.DISCONNECTED:
      active, terminal = False, False
      # A transient disconnect deliberately retains the assignment.
    elif event.kind is ConnectionEventKind.INVALIDATED:
      active, terminal = False, True
      self._assignments[key] = replace(assignment, state=AssignmentState.STARTING)
    elif event.kind is ConnectionEventKind.CLOSED:
      active, terminal = False, True
      self._assignments[key] = replace(assignment, state=AssignmentState.ABANDONED)
    else:
      active, terminal = False, False
    observed = ObservedConnection(
      instance_id,
      event.shard_id,
      connection_id,
      event.kind,
      active,
      terminal,
    )
    self._connections[key] = observed
    return observed

  def declare_dead(self, instance_id: str) -> tuple[str, ...]:
    removed_connections: list[str] = []
    for key, assignment in tuple(self._assignments.items()):
      if assignment.instance_id != instance_id:
        continue
      self._assignments[key] = replace(assignment, state=AssignmentState.ABANDONED)
      observed = self._connections.get(key)
      if observed is not None:
        if observed.connection_id is not None:
          removed_connections.append(observed.connection_id)
        self._connections[key] = replace(
          observed,
          event=ConnectionEventKind.CLOSED,
          active=False,
          terminal=True,
        )
    return tuple(removed_connections)

  def active_shards(self, instance_id: str) -> tuple[int, ...]:
    return tuple(
      shard_id
      for (owner, shard_id), connection in self._connections.items()
      if owner == instance_id
      and connection.active
      and self._assignments[(owner, shard_id)].state
      in {AssignmentState.ACTIVE, AssignmentState.DRAINING}
    )

  def active_owner(self, shard_id: int, shard_count: int) -> str | None:
    owners = [
      assignment.instance_id
      for assignment in self._assignments.values()
      if assignment.shard_id == shard_id
      and assignment.shard_count == shard_count
      and assignment.state is AssignmentState.ACTIVE
    ]
    if len(owners) > 1:
      raise RuntimeError("Multiple active Gateway assignments own one shard.")
    return owners[0] if owners else None


__all__ = (
  "AssignmentState",
  "GatewayState",
  "ObservedConnection",
  "ShardAssignment",
)
