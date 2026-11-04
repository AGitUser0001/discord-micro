"""Generate builtin EventSchema objects from Discord dispatch models."""

import argparse
import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, get_args

_HEADER = '''"""Generated Discord Gateway event schemas. Do not edit by hand."""

from micro.discord.models import gateway
from micro.service import DispatchSchema

'''

_LONG_EVENT = '''{event} = DispatchSchema[
  {payload}
](
  id={event!r},
  payload={payload},
)
'''

_SHORT_EVENT = '''{event} = DispatchSchema[{payload}](
  id={event!r},
  payload={payload},
)
'''

_FOOTER = '''
__all__ = (
{exports}
)
'''


@dataclass(frozen=True, slots=True)
class Dispatch:
  event: str
  payload: str


def _load(source: Path) -> ModuleType:
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
    dispatches.append(Dispatch(event_values[0], payload))
  if not dispatches:
    raise ValueError("No Discord Gateway dispatch models were found.")
  events = [dispatch.event for dispatch in dispatches]
  if len(events) != len(set(events)):
    raise ValueError("Discord Gateway dispatch event names are not unique.")
  return tuple(sorted(dispatches, key=lambda dispatch: dispatch.event))


def generate(source: Path, output: Path) -> None:
  dispatches = _dispatches(source)
  events = "\n".join(
    (
      _SHORT_EVENT
      if len(f"{item.event} = DispatchSchema[{item.payload}](") <= 88
      else _LONG_EVENT
    ).format(event=item.event, payload=item.payload)
    for item in dispatches
  )
  exports = "\n".join(f"  {item.event!r}," for item in dispatches)
  output.parent.mkdir(parents=True, exist_ok=True)
  output.write_text(_HEADER + events + _FOOTER.format(exports=exports))


def main() -> None:
  parser = argparse.ArgumentParser()
  parser.add_argument("source", type=Path)
  parser.add_argument("output", type=Path)
  arguments = parser.parse_args()
  generate(arguments.source, arguments.output)


if __name__ == "__main__":
  main()
