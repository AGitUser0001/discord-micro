"""Interaction routes: which one service owns an interaction."""

import re
from collections.abc import Mapping
from typing import Any

from micro import subjects

_SAFE = re.compile(r"[A-Za-z0-9_-]+")

APPLICATION_COMMAND = 2
MESSAGE_COMPONENT = 3
AUTOCOMPLETE = 4
MODAL_SUBMIT = 5

SLASH = 1
USER = 2
MESSAGE = 3


def route_token(value: str) -> str:
  """Encode any string as one subject token; safe values stay readable."""
  if _SAFE.fullmatch(value):
    return value
  return "%" + value.encode().hex()


def command_route(command_type: int, name: str) -> str:
  return f"cmd.{command_type}.{route_token(name)}"


def component_route(prefix: str) -> str:
  return f"cmp.{route_token(prefix)}"


def modal_route(prefix: str) -> str:
  return f"mdl.{route_token(prefix)}"


def custom_id_prefix(custom_id: str) -> str:
  """The routing prefix of a custom ID: everything before the first ':'."""
  return custom_id.partition(":")[0]


def interaction_route(payload: Mapping[str, Any]) -> str | None:
  """The route of an INTERACTION_CREATE payload, or None if it has none."""
  kind = payload.get("type")
  data = payload.get("data")
  if not isinstance(data, Mapping):
    return None
  if kind in (APPLICATION_COMMAND, AUTOCOMPLETE):
    name = data.get("name")
    command_type = data.get("type", SLASH)
    if isinstance(name, str) and isinstance(command_type, int):
      return command_route(command_type, name)
  elif kind in (MESSAGE_COMPONENT, MODAL_SUBMIT):
    custom_id = data.get("custom_id")
    if isinstance(custom_id, str):
      prefix = custom_id_prefix(custom_id)
      return (
        component_route(prefix) if kind == MESSAGE_COMPONENT else modal_route(prefix)
      )
  return None


def interaction_subject(route: str) -> str:
  return subjects.interaction(route)
