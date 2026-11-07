Components and modals
=====================

:class:`Components` handles button clicks and select-menu choices; :class:`Modals` handles
modal submissions. Both claim **custom IDs**: the string you put on a component when you
send it and that Discord returns when someone uses it. How you build the components is in
:doc:`ui`; how you read what was chosen or typed is in :doc:`responding`.

.. code-block:: python

   from pydantic import BaseModel
   from micro.discord.interactions import Components, CustomId, Modals
   from micro.discord.ui import Button, Modal, TextInput

   class Ticket(BaseModel):
     id: int

   CLOSE = CustomId("ticket.close", Ticket)        # encodes as "ticket.close:[42]"
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

Typed state: ``CustomId``
-------------------------

A :class:`CustomId` is a route that owns its prefix (the part before the first ``:``) and
carries a Pydantic model as state. ``encode(state)`` writes ``prefix:[v1,v2,...]``, the
field values in declaration order as compact JSON, so state costs only its values.
``decode`` turns it back; the handler receives the decoded model as its second argument.

* It must fit Discord's 100 characters (:data:`CUSTOM_ID_LIMIT`). ``encode`` raises
  ``ValueError`` if it does not, naming the length.
* The prefix is non-empty and contains no ``:``.
* **Evolve state append-only**: add new fields last and optional, and old buttons already
  in channels keep working (a missing trailing value takes its default, and trailing
  ``None``\ s are not encoded). Use a **new prefix** for a breaking change.

Matching other shapes
---------------------

``match`` accepts a route in several forms. The service *declares* the route, but the
**router** evaluates it, so the right service's queue gets the interaction.

.. code-block:: python

   import re

   @components.match("ticket.close")                      # that prefix, and ticket.close.* / ticket.close:*
   async def close(ctx): ...

   @components.match("ticket.{action}:{id:\\d+}")          # a template; {name} is one segment
   async def ticket(ctx): ctx.route                       # {"action": "close", "id": "42"}

   components.match(re.compile(r"report\.(?P<kind>spam|abuse)"))(report)

A route is a literal ``prefix`` plus an optional regex (:class:`PatternRoute`). Named groups
become ``ctx.route``. The router indexes routes by prefix, so many routes cost a few
dictionary lookups, not a regex scan. If several routes match one ID the **longest prefix
wins** and a warning names them. An ID no declared route matches falls back to its prefix
(before the first ``:``); with nobody handling that, the user gets the "isn't available"
reply.

Custom routes
~~~~~~~~~~~~~

For logic a pattern cannot express, subclass :class:`Route` (``match``, ``dump``, ``load``)
and pass an instance to ``match``. The router rebuilds the route from ``dump()`` by importing
its class, so **the router needs the same package** (an unimportable route is logged and
skipped) and ``dump()`` must hold no secrets: ``load()`` reads them from the router's own
environment.

Reading input
-------------

For a modal, ``ctx.inputs`` / ``ctx.fields`` and for a select ``ctx.values`` /
``ctx.users()`` and friends are described in :doc:`responding`.

Modals can be opened from a command, a component, or another modal's flow: ``await
ctx.modal(modal)`` must be the interaction's **first response**.

Reference
---------

.. api::
   micro.discord.interactions.Components
   micro.discord.interactions.Modals
   micro.discord.interactions.CustomId
   micro.discord.interactions.Route
   micro.discord.interactions.PatternRoute
   micro.discord.interactions.CUSTOM_ID_LIMIT
