"""Custom commands your members make: `/custom add hello Hi there!`, then `/hello`.

Needs a store and a command sync in micro.toml (`micro.store:Store`,
`micro.discord.interactions:CommandSync`). Each guild gets its own commands: the
command names are made at runtime (`RuntimeCommands`) and their text lives in the
store, so they survive restarts and work from every replica.
"""

from typing import Annotated

from micro.discord import Commands, Context, Draft, Err, Interaction, Ok, Option
from micro.discord.interactions import RuntimeCommands
from micro.service import Service
from micro.store import Conflict, GraphModule, StoreClient

CUSTOM = GraphModule(
  id="example.custom",
  schema="""
    type Guild @entity(key: ["id"]) {
      id: ID!
      commands: [Custom!]!
    }

    type Custom @entity(key: ["guildId", "name"]) {
      guildId: ID!
      name: String!
      text: String!
    }

    type Query {
      guild(id: ID!): Guild @from(key: {id: id})
      custom(guildId: ID!, name: String!): Custom
        @from(key: {guildId: guildId, name: name})
    }

    type Mutation {
      addGuild(id: ID!): Guild! @insert(key: {id: id}, set: {id: id})
      addCustom(guildId: ID!, name: String!, text: String!): Custom!
        @insert(key: {guildId: guildId, name: name},
                set: {guildId: guildId, name: name, text: text})
      attach(guildId: ID!, name: String!): Boolean
        @connect(fromType: "Guild", fromKey: {id: guildId},
                 toType: "Custom", toKey: {guildId: guildId, name: name},
                 field: "commands")
      editCustom(guildId: ID!, name: String!, text: String!): Custom
        @update(key: {guildId: guildId, name: name}, set: {text: text})
      removeCustom(guildId: ID!, name: String!): Boolean
        @delete(type: "Custom", key: {guildId: guildId, name: name})
    }
  """,
)

service = Service("custom")
service.uses(CUSTOM)
commands = Commands(service)
dynamic = RuntimeCommands(service)
custom = commands.group("custom", description="Custom commands for this server")


def store() -> StoreClient:
  return StoreClient(service.client)


@dynamic.handler
async def run(ctx: Context, interaction: Interaction) -> None:
  data = (
    await store().execute(
      t"{{ custom(guildId: {interaction.guild_id}, name: {interaction.command_name}) "
      t"{{ text }} }}"
    )
  ).unwrap()
  found = data.get("custom") or {}
  await interaction.respond(
    Draft(found.get("text") or "That command was removed.", ephemeral=True)
  )


@custom.command("add", description="Make a command (or change its text)")
async def add(
  ctx: Context,
  interaction: Interaction,
  name: Annotated[str, Option("Its name, lowercase", max_length=32)],
  text: Annotated[str, Option("What it says", max_length=2000)],
) -> None:
  if interaction.guild_id is None:
    await interaction.respond(Draft("Only in servers.", ephemeral=True))
    return
  name = name.lower().lstrip("/")
  if name == "custom":
    await interaction.respond(Draft("That name is taken.", ephemeral=True))
    return
  (
    await store().execute(
      t"mutation {{ addGuild(id: {interaction.guild_id}) {{ id }} }}"
    )
  ).ignore(Conflict)  # made now, or already there
  guild = interaction.guild_id
  match await store().execute(
    t"""
    mutation {{
      addCustom(guildId: {guild}, name: {name}, text: {text}) {{ name }}
      attach(guildId: {guild}, name: {name})
    }}
    """
  ):
    case Ok():
      pass
    case Err(Conflict()):  # it exists: change its text
      (
        await store().execute(
          t"mutation {{ editCustom(guildId: {guild}, name: {name}, text: {text}) "
          t"{{ name }} }}"
        )
      ).unwrap()
    case Err(error):
      raise error
  try:
    await dynamic.add(name, "Custom command", guild_id=interaction.guild_id)
  except ValueError:
    await interaction.respond(
      Draft("Names are lowercase letters, digits, - and _.", ephemeral=True)
    )
    return
  await interaction.respond(
    Draft(f"Made /{name}. It shows up in a moment.", ephemeral=True)
  )


@custom.command("remove", description="Delete a command")
async def remove(
  ctx: Context, interaction: Interaction, name: Annotated[str, Option("Its name")]
) -> None:
  name = name.lower().lstrip("/")
  data = (
    await store().execute(
      t"mutation {{ removeCustom(guildId: {interaction.guild_id}, name: {name}) }}"
    )
  ).unwrap()
  gone = data.get("removeCustom") is True
  if gone and interaction.guild_id is not None:
    await dynamic.remove(name, guild_id=interaction.guild_id)
  await interaction.respond(
    Draft(f"Removed /{name}." if gone else "No such command.", ephemeral=True)
  )


@custom.command("list", description="Show this server's custom commands")
async def list_commands(ctx: Context, interaction: Interaction) -> None:
  data = (
    await store().execute(
      t"{{ guild(id: {interaction.guild_id}) {{ commands {{ name }} }} }}"
    )
  ).unwrap()
  guild = data.get("guild") or {}
  names = sorted(item["name"] for item in guild.get("commands") or [])
  await interaction.respond(
    Draft(" ".join(f"`/{name}`" for name in names) or "None yet.", ephemeral=True)
  )
