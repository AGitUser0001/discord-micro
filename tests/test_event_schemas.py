import subprocess
import sys
from pathlib import Path
from typing import get_args

from micro.discord.models import gateway
from micro.discord.models.gateway import (
  APIInteraction,
  GatewayMessageCreateDispatchData,
)
from micro.schemas import events
from micro.service import EventSchema


def test_builtin_gateway_events_use_dispatch_names_and_data_models() -> None:
  assert isinstance(events.MESSAGE_CREATE, EventSchema)
  assert events.MESSAGE_CREATE.id == "MESSAGE_CREATE"
  assert events.MESSAGE_CREATE.payload is GatewayMessageCreateDispatchData
  assert events.INTERACTION_CREATE.id == "INTERACTION_CREATE"
  assert events.INTERACTION_CREATE.payload is APIInteraction


def test_builtin_gateway_event_exports_are_complete_and_unique() -> None:
  dispatches = get_args(gateway.GatewayDispatchPayload.model_fields["root"].annotation)
  expected = {
    get_args(dispatch.model_fields["t"].annotation)[0] for dispatch in dispatches
  }
  assert set(events.__all__) == expected
  assert all(getattr(events, name).id == name for name in events.__all__)


def test_gateway_event_schema_generation_is_reproducible(tmp_path: Path) -> None:
  generated = tmp_path / "events.py"
  subprocess.run(
    (
      sys.executable,
      "scripts/generate_events.py",
      "src/micro/discord/models/gateway.py",
      str(generated),
    ),
    check=True,
  )
  assert generated.read_bytes() == Path("src/micro/schemas/events.py").read_bytes()
