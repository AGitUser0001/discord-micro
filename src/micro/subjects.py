"""Every NATS subject, stream, consumer, and bucket name Micro uses.

Nothing else in Micro writes these names by hand, so the complete wire layout
is readable here.
"""

import hashlib
import re

PREFIX = "micro"

EVENTS_STREAM = "MICRO_EVENTS"
"""Interest-retention stream holding application events, Discord dispatches,
standby dispatches, and Gateway connection lifecycle events."""

EVENT_STREAM_SUBJECTS = (
  "micro.evt.>",
  "micro.discord.dispatch.>",
  "micro.discord.standby.>",
  "micro.gateway.connection.>",
)

RETIRED_EVENT_STREAM_SUBJECTS = ("micro.discord.interaction.>",)
"""Subjects earlier versions put in MICRO_EVENTS; removed on start."""

INTERACTIONS_STREAM = "MICRO_INTERACTIONS"
"""Work-queue stream of routed interactions, one consumer per route. Messages
carry a TTL of Discord's response deadline, so nothing is delivered late."""

INTERACTION_SUBJECTS = ("micro.discord.interaction.>",)

WORK_STREAM_PREFIX = "MICRO_WORK_"

PRESENCE_BUCKET = "micro_presence"
"""Live component registrations; every key carries a TTL and is renewed."""

SHARDS_BUCKET = "micro_shards"
"""Gateway shard leases, `<generation>.<shard_id>`."""

GATEWAY_BUCKET = "micro_gateway"
"""Gateway desired generation, active generation, and desired presence."""

LOCKS_BUCKET = "micro_locks"
"""One-time job leases such as identify buckets and command sync."""

PAYLOADS_BUCKET = "micro_payloads"
"""Object store for request/reply bodies above the NATS message limit."""

STATE_BUCKET = "micro_state"
"""Small durable coordination values without a TTL, such as definition hashes."""

HTTP_GLOBAL_LIMIT = "micro.ratelimit.discord.global"
"""Core NATS broadcast announcing a Discord global rate limit."""

_TOKEN = re.compile(r"[A-Za-z0-9_-]+")
_DOTTED = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?")


def token(value: str) -> str:
  """Validate one subject token (no dots or wildcards)."""
  if _TOKEN.fullmatch(value) is None:
    raise ValueError(f"{value!r} is not a valid subject token.")
  return value


def dotted(value: str) -> str:
  """Validate a dotted identifier such as a request or event ID."""
  if _DOTTED.fullmatch(value) is None or ".." in value:
    raise ValueError(f"{value!r} is not a valid dotted identifier.")
  return value


def request(request_id: str) -> str:
  """Request/reply subject; replicas share the queue group of the same name."""
  return f"micro.req.{dotted(request_id)}"


def event(event_id: str) -> str:
  return f"micro.evt.{dotted(event_id)}"


def dispatch(name: str, guild_id: int | str | None = None) -> str:
  """Subject of one raw Gateway dispatch published by a shard's owner."""
  return f"micro.discord.dispatch.{token(name)}.{_guild(guild_id)}"


def dispatch_filter(name: str = "*", guild_id: int | str | None = "*") -> str:
  event_name = name if name == "*" else token(name)
  guild = "*" if guild_id == "*" else _guild(guild_id)
  return f"micro.discord.dispatch.{event_name}.{guild}"


def standby(name: str, guild_id: int | str | None = None) -> str:
  """Dispatches from connections that are not publishing (projection only)."""
  return f"micro.discord.standby.{token(name)}.{_guild(guild_id)}"


def interaction(route: str) -> str:
  """An interaction routed to the one service owning `route` (see micro.discord.interactions)."""
  return f"micro.discord.interaction.{route}"


def connection(shard_id: int) -> str:
  return f"micro.gateway.connection.{shard_id}"


def gateway_control(shard_id: int, operation: str) -> str:
  return f"micro.gateway.ctl.{shard_id}.{token(operation)}"


def http_worker(instance: str) -> str:
  return f"micro.discord.http.{token(instance)}"


def work(queue: str) -> str:
  return f"micro.work.{dotted(queue)}"


def work_stream(queue: str) -> str:
  return WORK_STREAM_PREFIX + safe_name(queue).upper()


def supervisor(deployment: str, operation: str) -> str:
  """Control subjects of the `micro up` supervisor for one deployment."""
  return f"micro.supervisor.{token(deployment)}.{token(operation)}"


def durable(kind: str, name: str) -> str:
  """A JetStream consumer name for one logical component."""
  return f"{token(kind)}_{safe_name(name)}"


def _guild(guild_id: int | str | None) -> str:
  if guild_id is None:
    return "_"
  value = str(guild_id)
  if not value.isdecimal():
    raise ValueError(f"{guild_id!r} is not a guild ID.")
  return value


def safe_name(name: str) -> str:
  """Map a dotted name to a token, keeping it unique and readable."""
  readable = re.sub(r"[^A-Za-z0-9_-]", "_", name)
  if readable == name:
    return name
  digest = hashlib.sha256(name.encode()).hexdigest()[:8]
  return f"{readable}_{digest}"


__all__ = (
  "EVENTS_STREAM",
  "EVENT_STREAM_SUBJECTS",
  "GATEWAY_BUCKET",
  "HTTP_GLOBAL_LIMIT",
  "INTERACTIONS_STREAM",
  "INTERACTION_SUBJECTS",
  "LOCKS_BUCKET",
  "PAYLOADS_BUCKET",
  "PREFIX",
  "PRESENCE_BUCKET",
  "RETIRED_EVENT_STREAM_SUBJECTS",
  "SHARDS_BUCKET",
  "STATE_BUCKET",
  "WORK_STREAM_PREFIX",
  "connection",
  "dispatch",
  "dispatch_filter",
  "dotted",
  "durable",
  "event",
  "gateway_control",
  "http_worker",
  "interaction",
  "request",
  "safe_name",
  "standby",
  "supervisor",
  "token",
  "work",
  "work_stream",
)
