"""Introspection: `/health` (admins only) shows streams, consumers and who is running.

Everything it reports comes from JetStream and the presence directory, so it works
on any deployment. `report(runtime)` returns the same numbers for your own code.
"""

from collections import Counter
from collections.abc import Sequence
from typing import Any

from micro.discord.interactions import Commands, Context, Interaction
from micro.discord.ui import Draft
from micro.runtime import Runtime
from micro.service import Service

ADMINISTRATOR = 1 << 3

service = Service("health")
commands = Commands(service)


async def report(runtime: Runtime) -> dict[str, Any]:
  """Streams (messages, consumers, backlog) and the live components, by kind."""
  js = runtime.jetstream
  account = await js.account_info()
  streams: list[dict[str, Any]] = []
  for stream in await js.streams_info():
    consumers = await js.consumers_info(stream.config.name or "")
    streams.append(
      {
        "stream": stream.config.name,
        "messages": stream.state.messages,
        "consumers": len(consumers),
        "ephemeral": sum(1 for c in consumers if not c.config.durable_name),
        "pending": sum(c.num_pending or 0 for c in consumers),
        "unacked": sum(c.num_ack_pending or 0 for c in consumers),
      }
    )
  kinds = Counter(entry.kind for entry in runtime.directory.entries())
  return {
    "streams": sorted(streams, key=lambda item: str(item["stream"])),
    "consumers": account.consumers,
    "components": dict(sorted(kinds.items())),
  }


def table(headers: Sequence[str], rows: Sequence[Sequence[object]]) -> str:
  cells = [[str(cell) for cell in row] for row in (headers, *rows)]
  widths = [max(len(cell) for cell in column) for column in zip(*cells)]

  def line(row: Sequence[str]) -> str:
    return "| " + " | ".join(c.ljust(w) for c, w in zip(row, widths)) + " |"

  rule = "| " + " | ".join("-" * width for width in widths) + " |"
  return "\n".join([line(cells[0]), rule, *map(line, cells[1:])])


@commands.slash(
  "health",
  description="Streams, consumers and running components",
  default_member_permissions=ADMINISTRATOR,
)
async def health(ctx: Context, interaction: Interaction) -> None:
  await interaction.defer(ephemeral=True)
  data = await report(service.runtime)
  streams = table(
    ["stream", "messages", "consumers", "ephemeral", "pending", "unacked"],
    [list(item.values()) for item in data["streams"]],
  )
  running = table(["kind", "count"], list(data["components"].items()))
  await interaction.respond(
    Draft(
      f"**{data['consumers']}** consumers in total\n```\n{streams}\n\n{running}\n```",
      ephemeral=True,
    )
  )
