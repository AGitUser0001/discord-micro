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

Components
----------

Every component Discord has, from ``micro.discord.ui``; ``ui.validate(...)`` checks any
of them against Discord's request models (limits included) and anything missing can be
passed as a plain dict.

.. code-block:: python

   from micro.discord.ui import *

   # Classic: up to five buttons, or one select, per row (loose ones are laid out).
   Button("Go", custom_id="go", style="success", emoji="🚀")      # also url=, or sku_id= (premium)
   StringSelect("pick", ["a", SelectOption("B", "b", "second", emoji="🅱")], max_values=2)
   UserSelect("who", defaults=[123]); RoleSelect("role")
   MentionableSelect("m", defaults=[Default.user(1), Default.role(2)])
   ChannelSelect("where", channel_types=["text", "voice", "category"])

   # Layout (v2): sets IS_COMPONENTS_V2 for you; no content or embeds, only these.
   Container(
     TextDisplay("## Report"),
     Section("**Ada** opened this", "2 days ago", accessory=Thumbnail("https://.../a.png")),
     Separator(),
     MediaGallery("https://.../1.png", MediaItem("attachment://2.png", "alt text")),
     File("attachment://report.pdf"),
     ActionRow(Button("Close", custom_id="close")),
     accent_color=0x5865F2,
   )

   # Modals: Label wraps one input; TextDisplay explains.
   Modal("form", "Report", [
     TextDisplay("Tell us what happened."),
     Label("Summary", TextInput("summary", max_length=100)),
     Label("Details", TextInput("details", style="paragraph", required=False)),
     Label("Kind", StringSelect("kind", ["bug", "abuse"])),
     Label("Who", UserSelect("who")),
     Label("Evidence", FileUpload("files", max_values=3)),
     Label("Severity", RadioGroup("severity", ["low", "high"])),
     Label("Notify", CheckboxGroup("notify", ["me", "staff"])),
     Label("Confirm", Checkbox("sure")),
   ])

A modal submission is read with ``ctx.inputs`` (everything, by ``custom_id``: strings for
text and radio, lists for selects, checkbox groups and uploads, a bool for a checkbox),
``ctx.fields`` (just the text-like ones, as strings), and for the entity fields
``ctx.users("who")``, ``ctx.members(...)``, ``ctx.roles(...)``, ``ctx.channels(...)`` and
``ctx.attachments("files")``. A select on a message works the same without the name
(``ctx.users()``), and ``ctx.resolved`` holds all of Discord's lookup table.

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
If several routes match one ID, the longest prefix wins and a warning names them.
An ID no declared route matches falls back to its prefix (before the first
``:``) and, with nobody handling that, gets the "isn't available" reply.

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

Commands made while running
---------------------------

``Commands`` are fixed when the code is written. For commands users create (a bot's
custom commands, per-guild commands), use ``RuntimeCommands``: you add and remove
commands from code that is already running, and one handler runs all of them.

.. code-block:: python

   from micro.discord.interactions import RuntimeCommands, option

   dynamic = RuntimeCommands(service)

   @dynamic.handler
   async def run(ctx: Interaction) -> None:
     body = await lookup(ctx.guild_id, ctx.command_name)   # your own storage
     await ctx.respond(body)

   await dynamic.add("hello", "Say hello", guild_id=1234,
                     options=[option("who", "Who to greet")])
   await dynamic.remove("hello", guild_id=1234)

* ``add`` creates a command or changes its definition. Without ``guild_id`` it is a
  global command. Adding the same name for another guild adds a scope: it is one
  command, so use ``ctx.guild_id`` to tell guilds apart. ``remove`` drops one scope,
  and the command goes when its last scope does.
* Options arrive in ``ctx.option_values`` (``{"who": "bo"}``) and ``ctx.command_name``
  is the name. Pass ``kind=2`` or ``3`` for user and message context menus.
* ``@dynamic.autocomplete`` takes ``async def f(ctx, value)`` and returns choices for
  options you described with ``autocomplete=True`` in a raw option dict.
* Commands are stored by the runtime, so they survive restarts, work from every
  replica, and ``CommandSync`` registers them within moments. They are applied right
  away, not held back by a rolling update. A name also declared in code is skipped
  (the declared one wins). The text of a custom command belongs in your own storage
  (``store`` or a database); this only manages the commands themselves.

Interactions over HTTP
----------------------

Instead of the Gateway, Discord can POST each interaction to a URL you give it in the
developer portal (*Interactions Endpoint URL*). ``InteractionEndpoint`` is that URL:
swap it in where ``GatewayWorker`` was and nothing else changes. The router, commands,
components, modals, middleware, ``CommandSync`` and runtime commands all work as before.

.. code-block:: toml

   [processes.http]
   components = ["micro.discord.interactions:InteractionEndpoint"]
   replicas = 2                      # any number, behind one URL
   env = { DISCORD_PUBLIC_KEY = "...", MICRO_HTTP_PORT = "8081" }

Install it with ``pip install "micro[http]"`` (a web server; nothing for the signatures, which are checked in plain Python). Put TLS in front of it (a reverse proxy
or tunnel): Discord only calls ``https`` URLs. The public key is on the application's
*General Information* page.

* Every request is checked against the key; a bad signature gets a 401, and Discord's
  PING gets its PONG.
* A request is held open until a handler gives its first response, and that response is
  the HTTP reply. Later calls (follow-ups, edits) use Discord's webhook endpoints.
  Handlers have Discord's 3 seconds, as ever: ``defer()`` first when unsure.
* Without the Gateway there are no events (``service.listen`` for messages, members and
  so on) and no member cache. HTTP is for bots that only answer commands and components.

Routing and sync
----------------

* Each route (a command name, or a declared custom ID route) has one durable
  consumer on the ``MICRO_INTERACTIONS`` work queue; every replica and version of
  every service handling it pulls from it. Any number of services may share a
  route.
* The router enqueues with a 3 s TTL (never delivered late) and deduplicates by
  interaction ID. If nothing handles a route, it replies ephemerally.
* ``ctx.age`` is the seconds since Discord created the interaction. A handler that
  starts more than 2 s into Discord's 3 s window logs a warning, and a failure logs
  its age, so a ``10062 Unknown interaction`` shows whether the time went before
  the handler (gateway, NATS, a skewed clock) or after it.
* ``CommandSync`` registers a definition only when every live replica agrees on
  it; stopping a service never unregisters commands. ``micro commands list``,
  ``micro commands forget TYPE:NAME``.
* Each scope (global, and every guild a command names) is registered on its own,
  global first, with one bulk overwrite that changes it atomically. A scope
  Discord refuses, such as a guild the bot left, is retried and reported once
  without holding up the others. A pass trusts its own record, but the first
  pass after ``CommandSync`` starts, and ``micro commands sync``, also compare
  with what Discord has and repair commands deleted or edited elsewhere.
