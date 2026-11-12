"""Generate the lazily created builtin dispatch schemas.

`source` is a generated gateway model file, or the dotted name of the split
model package (for example `micro.discord.models.gateway`).
"""

import argparse
import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, get_args

_HEADER = '''"""Generated Discord Gateway event schemas. Do not edit by hand.

Each schema, and the payload model it validates, is created on first use.
"""

from typing import TYPE_CHECKING, Any

from micro.service import DispatchSchema

if TYPE_CHECKING:
  from micro.discord import objects
  from micro.discord.models import gateway

'''

_FOOTER = '''

def __getattr__(name: str) -> Any:
  try:
    payload = _PAYLOADS[name]
  except KeyError:
    raise AttributeError(f"module {{__name__!r}} has no attribute {{name!r}}") from None
  from micro.discord import objects
  from micro.discord.models import gateway

  schema = DispatchSchema[Any](
    id=name,
    payload=None
    if payload is None
    else getattr(objects if payload in _VIEWS else gateway, payload),
  )
  globals()[name] = schema
  return schema


def __dir__() -> list[str]:
  return sorted(_PAYLOADS)


__all__ = (
{exports}
)
'''


VIEWS = {
  "CHANNEL_CREATE": "Channel",
  "CHANNEL_DELETE": "Channel",
  "CHANNEL_UPDATE": "Channel",
  "GUILD_CREATE": "Guild",
  "GUILD_MEMBER_ADD": "Member",
  "GUILD_MEMBER_UPDATE": "Member",
  "GUILD_UPDATE": "Guild",
  "MESSAGE_CREATE": "Message",
  "MESSAGE_UPDATE": "Message",
  "THREAD_CREATE": "Channel",
  "THREAD_UPDATE": "Channel",
  "USER_UPDATE": "User",
}
"""The events whose payload is one of Micro's objects: a handler gets it bound to its
`Context`, with `.before` when the event changed it."""


@dataclass(frozen=True, slots=True)
class Dispatch:
  event: str
  payload: str


def _load(source: Path) -> ModuleType:
  if not source.exists():
    return importlib.import_module(str(source))
  name = "_micro_generated_gateway_models"
  specification = importlib.util.spec_from_file_location(name, source)
  if specification is None or specification.loader is None:
    raise ValueError(f"Cannot import generated Gateway models from {source}.")
  module = importlib.util.module_from_spec(specification)
  sys.modules[name] = module
  try:
    specification.loader.exec_module(module)
  finally:
    sys.modules.pop(name, None)
  return module


def _dispatches(source: Path) -> tuple[Dispatch, ...]:
  module = _load(source)
  root = module.GatewayDispatchPayload.model_fields["root"].annotation
  dispatches: list[Dispatch] = []
  for dispatch in get_args(root):
    fields: dict[str, Any] = dispatch.model_fields
    event_values = get_args(fields["t"].annotation)
    if len(event_values) != 1 or not isinstance(event_values[0], str):
      raise TypeError(f"{dispatch.__name__}.t is not one string literal.")
    payload_type = fields["d"].annotation if "d" in fields else type(None)
    payload = (
      "None" if payload_type is type(None) else f"gateway.{payload_type.__name__}"
    )
    if event_values[0] in VIEWS:
      payload = f"objects.{VIEWS[event_values[0]]}"
    dispatches.append(Dispatch(event_values[0], payload))
  if not dispatches:
    raise ValueError("No Discord Gateway dispatch models were found.")
  events = [dispatch.event for dispatch in dispatches]
  if len(events) != len(set(events)):
    raise ValueError("Discord Gateway dispatch event names are not unique.")
  return tuple(sorted(dispatches, key=lambda dispatch: dispatch.event))


def generate(source: Path, output: Path) -> None:
  dispatches = _dispatches(source)
  annotations = "\n".join(
    f"  {item.event}: DispatchSchema[{item.payload}]" for item in dispatches
  )
  payloads = "\n".join(
    f"  {item.event!r}: "
    + (
      "None"
      if item.payload == "None"
      else repr(item.payload.removeprefix("gateway.").removeprefix("objects."))
    )
    + ","
    for item in dispatches
  )
  views = "\n".join(f"  {name!r}," for name in sorted(set(VIEWS.values())))
  exports = "\n".join(f"  {item.event!r}," for item in dispatches)
  output.parent.mkdir(parents=True, exist_ok=True)
  output.write_text(
    _HEADER
    + annotations
    + "\n\n_PAYLOADS: dict[str, str | None] = {\n"
    + payloads
    + "\n}\n\n_VIEWS = {\n"
    + views
    + "\n}\n"
    + _FOOTER.format(exports=exports)
  )


def main() -> None:
  parser = argparse.ArgumentParser()
  parser.add_argument("source", type=Path)
  parser.add_argument("output", type=Path)
  arguments = parser.parse_args()
  generate(arguments.source, arguments.output)


if __name__ == "__main__":
  main()
