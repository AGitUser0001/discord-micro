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

   @commands.slash("ticket", description="Open a ticket")
   async def ticket(
     ctx: Interaction,
     topic: Annotated[str, Option("What about", max_length=100)],
     level: Literal["low", "high"] = "low",
     assignee: User | None = None,
   ) -> None:
     await ctx.respond(f"Opened {topic}")

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

   @components.match(CLOSE)
   async def close(ctx: Interaction, ticket: Ticket) -> None:
     await ctx.update_message(f"Ticket {ticket.id} closed.", components=[])

   @modals.match(NOTE)
   async def note(ctx: Interaction) -> None:
     await ctx.respond(ctx.fields["text"], ephemeral=True)

   Button("Close", custom_id=CLOSE.encode(Ticket(id=42)))
   Modal(NOTE.encode(), "Add a note", [TextInput("text", "Note", style="paragraph")])

``CustomId`` fits Discord's 100 characters. Evolve its state append-only
(new fields last and optional) so old buttons keep working; use a new prefix
for breaking changes.

Responding
----------

``respond`` is the everyday call; it picks the right Discord request from what
the interaction has already sent.

.. code-block:: python

   await ctx.respond("hi", ephemeral=True, embeds=[...], components=[...])
   await ctx.defer()                      # button: silent, update mode. Command: "thinking..."
   await ctx.defer(thinking=True)         # button: "thinking..." (message mode)
   await ctx.edit_response("changed")
   await ctx.delete_response()
   await ctx.update_message("new content")   # edit the message a button sits on
   await ctx.modal(modal)
   await ctx.autocomplete(["a", "b"])

======================  =======  ==============  ================  ===========
after →                 nothing  ``defer()``     ``defer(think)``  responded
======================  =======  ==============  ================  ===========
``respond``             new      follow-up       fills "thinking"  follow-up
``update_message``      edits    edits original  **error**         **error**
======================  =======  ==============  ================  ===========

Wrong sequences raise ``InvalidResponse`` or ``AlreadyResponded`` naming the
state, before anything is sent. ``update_message`` needs the source message of a
component (or of a modal opened from one). Nothing defers automatically; an
unanswered interaction fails after Discord's 3 seconds. After 15 minutes, calls
raise ``InteractionExpired``.

The low-level layer is one Discord request each, never deciding or refusing:
``create_initial_response(ResponseType.X, data)``, ``create_followup(body)``,
``edit_initial_response(body)``, ``delete_initial_response()``. Context:
``ctx.user``, ``ctx.member``, ``ctx.guild_id``, ``ctx.channel_id``,
``ctx.custom_id``, ``ctx.values``, ``ctx.fields``, ``ctx.message``,
``ctx.locale``, ``ctx.state``.

Middleware
----------

``use`` wraps what happens around a handler, on any template and on the router
(the same engine as ``service.use`` in :doc:`services`).
Middleware nests in the order added; ``next()`` runs the rest, ``end()`` stops
the flow, and each pass must do exactly one of those (or raise). ``ctx`` is the
flow: ``ctx.interaction``, ``ctx.payload`` (Discord's JSON, editable before
``next()``), ``ctx.key``, ``ctx.service``, ``ctx.state``.

.. code-block:: python

   from micro.discord.interactions import defers

   @components.use
   async def staff_only(ctx, next, end):
     if not is_staff(ctx.interaction):
       await ctx.interaction.respond("Staff only.", ephemeral=True)
       return await end()
     await next()

   commands.use("admin", defers(ephemeral=True))     # scoped: "admin" and "admin.*"
   components.use("ticket", audit)                   # "ticket.close:[42]", "ticket:..."

   @router.use                                       # before routing: unwrap signed IDs
   async def unwrap(ctx, next, end):
     data = ctx.payload.get("data") or {}
     if "custom_id" in data:
       data["custom_id"] = codec.decode(data["custom_id"])   # routes by the real prefix
     await next()

A scope matches its key and anything nested under it (``.`` or ``:``
separated); a command's key is its dotted path, a component's its custom ID.
An error anywhere (middleware, a custom ID that will not decode, a handler)
gets one ephemeral "Something went wrong." and a log entry; catch it in your own
middleware with ``try/except`` around ``next()`` to say something else. A flow
that ends without responding is logged.

Routing custom IDs
------------------

``components.match(route)`` (and ``modals.match``) is how a handler claims
custom IDs. The service declares the route, but the **router** evaluates it, so
the right service's queue gets the interaction. A ``CustomId`` is a route that
owns its prefix (before the first ``:``) and hands its decoded state to the
handler; a plain string owns that prefix and what is nested under it (``.`` or
``:``).

.. code-block:: python

   import re

   @components.match("ticket.{action}:{id:\\d+}")     # template; {name} is one segment
   async def ticket(ctx): ctx.route                  # {"action": "close", "id": "42"}

   components.match(re.compile(r"report\.(?P<kind>spam|abuse)"))(report)

A route is a literal ``prefix`` plus an optional regex (``PatternRoute``).
The router indexes routes by prefix, so many routes cost a few dict lookups.
Declared routes are tried before the plain prefix rule; if several match, the
longest prefix wins and a warning names them.

For logic a pattern cannot express, subclass ``Route`` (``match``, ``dump``,
``load``) and pass an instance to ``match``. The router rebuilds it from
``dump()`` by importing its class, so **the router needs the same package**
(an unimportable route is logged and skipped) and ``dump()`` must not hold
secrets: ``load()`` reads them from the router's own environment.

Customizing the router
----------------------

.. code-block:: python

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
* Each scope (global, and every guild a command names) is registered on its own,
  global first, with one bulk overwrite that changes it atomically. A scope
  Discord refuses, such as a guild the bot left, is retried and reported once
  without holding up the others. A pass trusts its own record, but the first
  pass after ``CommandSync`` starts, and ``micro commands sync``, also compare
  with what Discord has and repair commands deleted or edited elsewhere.
