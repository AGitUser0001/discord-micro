"""Notes kept in the store: `/note add`, `/note list`, and attached files.

Needs a store in micro.toml (`micro.store:Store`); the module below is declared
by this service, so the store serves it automatically.
"""

import base64
import time
from typing import Annotated

from micro.discord import Attachment, Commands, Context, Draft, Interaction, Option
from micro.service import Service
from micro.store import GraphModule, StoreClient

NOTES = GraphModule(
  id="example.notes",
  schema="""
    scalar Bytes

    type Note @entity(key: ["id"]) {
      id: ID!
      author: String!
      text: String!
      file: Bytes
    }

    type Query {
      note(id: ID!): Note @from(key: {id: id})
      notes(first: Int!, offset: Int!): [Note!]! @scan
    }

    type Mutation {
      addNote(id: ID!, author: String!, text: String!, file: Bytes): Note!
        @insert(key: {id: id}, set: {id: id, author: author, text: text, file: file})
    }
  """,
)

service = Service("notes")
service.uses(NOTES)
commands = Commands(service)
note = commands.group("note", description="Shared notes")


@note.command("add", description="Write a note, optionally with a file")
async def add(
  ctx: Context,
  interaction: Interaction,
  text: Annotated[str, Option("The note", max_length=1000)],
  file: Attachment | None = None,
) -> None:
  data = None
  if file is not None:
    import httpx2

    async with httpx2.AsyncClient() as http:
      data = base64.b64encode((await http.get(file.url)).content).decode()
  note_id, author = f"{time.time_ns()}", interaction.user.display_name
  (
    await StoreClient(service.client).execute(
      t"""
      mutation {{
        addNote(id: {note_id}, author: {author}, text: {text}, file: {data}) {{ id }}
      }}
      """
    )
  ).unwrap()
  await interaction.respond(Draft("Saved.", ephemeral=True))


@note.command("list", description="Show recent notes")
async def list_notes(ctx: Context, interaction: Interaction) -> None:
  data = (
    await StoreClient(service.client).execute(
      t"{{ notes(first: 10, offset: 0) {{ author text }} }}"
    )
  ).unwrap()
  notes = data.get("notes") or []
  lines = [f"**{item['author']}**: {item['text']}" for item in notes]
  await interaction.respond(Draft("\n".join(lines) or "No notes yet.", ephemeral=True))
