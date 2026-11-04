Interactions
============

Templates attach to any service. Run ``InteractionRouter`` and ``CommandSync``
once per deployment (any number of replicas).

.. code-block:: text

   GatewayWorker → INTERACTION_CREATE
     → InteractionRouter → per-route work queue (TTL 3 s)
       → Commands / Components / Modals on any service → Interaction → HTTP worker

Commands
--------

.. code-block:: python

   from typing import Annotated, Literal
   from micro.discord.interactions import Commands, Interaction, Option
   from micro.discord.objects import Member, Message, User

   commands = Commands(service, guild_ids=[...])   # guild_ids optional

   @commands.slash("ticket", description="Open a ticket", ephemeral_defer=True)
   async def ticket(
     ctx: Interaction,
     topic: Annotated[str, Option("What about", max_length=100)],
     level: Literal["low", "high"] = "low",
     assignee: User | None = None,
   ) -> None:
     await ctx.reply(f"Opened {topic}")

   @ticket.autocomplete("topic")
   async def topics(ctx: Interaction, value: str) -> list[str]:
     return [t for t in ("billing", "bug") if t.startswith(value)]

   admin = commands.group("admin", description="Admin tools")
   @admin.command("purge")
   async def purge(ctx: Interaction, count: int) -> None: ...

   @commands.user("Report")
   async def report(ctx: Interaction, member: Member) -> None: ...

   @commands.message("Quote")
   async def quote(ctx: Interaction, message: Message) -> None: ...

Option types: ``str``, ``int``, ``float``, ``bool``, ``User``, ``Member``,
``Role``, ``Channel``, ``Mentionable``, ``Attachment``, ``Literal[...]``.
Defaults make options optional. ``Option`` sets description, choices, limits,
channel types, and localizations.

Components and modals
---------------------

.. code-block:: python

   from pydantic import BaseModel
   from micro.discord.interactions import Components, CustomId, Modals
   from micro.discord.ui import Button, Modal, TextInput

   class Ticket(BaseModel):
     id: int

   CLOSE = CustomId("ticket.close", Ticket)        # "ticket.close:[42]"
   NOTE = CustomId("ticket.note")

   components, modals = Components(service), Modals(service)

   @components.on(CLOSE)
   async def close(ctx: Interaction, ticket: Ticket) -> None:
     await ctx.update(f"Ticket {ticket.id} closed.", components=[])

   @modals.on(NOTE)
   async def note(ctx: Interaction) -> None:
     await ctx.reply(ctx.fields["text"], ephemeral=True)

   Button("Close", custom_id=CLOSE.encode(Ticket(id=42)))
   Modal(NOTE.encode(), "Add a note", [TextInput("text", "Note", style="paragraph")])

``CustomId`` fits Discord's 100 characters. Evolve its state append-only
(new fields last and optional) so old buttons keep working; use a new prefix
for breaking changes.

Responding
----------

.. code-block:: python

   await ctx.reply("hi", ephemeral=True, embeds=[...], components=[...])  # follow-up if already answered
   await ctx.defer(ephemeral=True)       # "thinking…"; a later reply fills it in
   await ctx.followup("more")
   await ctx.edit("changed")
   await ctx.delete()
   await ctx.update("new content")       # component/modal: edit the message
   await ctx.modal(modal)
   await ctx.autocomplete(["a", "b"])

Handlers not answered within ``defer_after`` (1.5 s) are deferred
automatically. After 15 minutes, calls raise ``InteractionExpired``. Context:
``ctx.user``, ``ctx.member``, ``ctx.guild_id``, ``ctx.channel_id``,
``ctx.custom_id``, ``ctx.values``, ``ctx.fields``, ``ctx.message``, ``ctx.locale``.

Customizing templates
---------------------

Override hooks; the builtins use only public pieces.

.. code-block:: python

   class GuardedCommands(Commands):
     async def around(self, ctx, call):                # wrap every handler
       if not ctx.member or "123" not in ctx.member.roles:
         return await ctx.reply("Staff only.", ephemeral=True)
       await call()

     async def on_error(self, ctx, error):              # what users see on failure
       await ctx.reply("Oops, logged it.", ephemeral=True)

     def deferral(self, ctx):                           # True/False/None
       return True

   class GuildRouter(InteractionRouter):
     def route(self, payload):                          # also: owned(route), unroutable(payload)
       return super().route(payload)

A custom template subclasses ``InteractionTemplate`` (``routes()``,
``resolve(ctx)``), or implements ``start``/``stop``/``metadata`` from scratch.

Routing and sync
----------------

* Each route (command name or custom_id prefix) has one durable consumer on
  the ``MICRO_INTERACTIONS`` work queue; every replica and version of every
  service handling it pulls from it. Any number of services may share a route.
* The router enqueues with a 3 s TTL (never delivered late) and deduplicates by
  interaction ID. If nothing handles a route, it replies ephemerally.
* ``CommandSync`` registers a definition only when every live replica agrees on
  it; stopping a service never unregisters commands. ``micro commands list``,
  ``micro commands forget TYPE:NAME``.
