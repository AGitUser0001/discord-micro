Middleware
==========

Middleware wraps what happens around a handler. The same engine serves the **service** (every
request, event and job: ``service.use``, see :doc:`services`), every **interaction template**
(``commands.use``, ``components.use``, ``modals.use``) and the **router** (``router.use``).

Writing it
----------

A middleware is an ``async`` function. It receives the call context, ``next`` and (optionally)
``end``. Middleware nests in the order it was added; ``next()`` runs the rest of the chain
and the handler, ``end()`` stops without running the handler, and **each pass must do exactly
one of those, or raise**.

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

In an interaction template ``ctx`` is a :class:`Flow`: ``ctx.interaction`` (the
:class:`Interaction`), ``ctx.payload`` (Discord's JSON, editable before ``next()``),
``ctx.key`` (what scopes match), ``ctx.service`` and ``ctx.state``.

Scopes
------

``use("scope", fn)`` limits middleware to a key and anything nested under it. Keys are
dotted: a command's key is its path (``admin.purge``), a component's key is its custom ID,
and ``.`` or ``:`` both separate levels, so the scope ``"ticket"`` matches ``ticket``,
``ticket.close`` and ``ticket.close:[42]`` but not ``tickets``.

The router: before routing
--------------------------

``InteractionRouter.use`` runs **before routing** and may change the payload, so it can change
which service gets an interaction. A real use is **signing custom IDs**: anyone can forge the
``custom_id`` of a button (it is just a string the client sends back), so you sign the ones you
create and refuse any that do not verify. The router strips the signature, so the handlers
behind it keep matching their plain ``ticket.close:[42]`` ids and never see it.

The whole thing is three pieces: how IDs are signed, the router that checks them, and the
place you sign when sending.

.. code-block:: python

   # myapp/signing.py
   import hashlib
   import hmac
   import os

   SECRET = os.environ["CUSTOM_ID_SECRET"].encode()

   def _mac(custom_id: str) -> str:
     return hmac.new(SECRET, custom_id.encode(), hashlib.sha256).hexdigest()[:16]

   def sign(custom_id: str) -> str:
     """`ticket.close:[42]` becomes `ticket.close:[42]~<mac>` (still under Discord's 100)."""
     return f"{custom_id}~{_mac(custom_id)}"

   def verify(signed: str) -> str | None:
     """The original custom ID, or None if the signature does not match."""
     custom_id, _, mac = signed.rpartition("~")
     return custom_id if hmac.compare_digest(mac, _mac(custom_id)) else None

.. code-block:: python

   # myapp/router.py: the router, with the check as middleware
   from micro.discord.interactions import InteractionRouter

   from .signing import verify

   router = InteractionRouter()

   @router.use
   async def check_signature(ctx, next, end):
     data = ctx.payload.get("data") or {}
     signed = data.get("custom_id")
     if signed is not None:                      # a component or a modal submit
       custom_id = verify(signed)
       if custom_id is None:
         await ctx.interaction.respond("That button is no longer valid.", ephemeral=True)
         return await end()                      # never routed, no handler runs
       data["custom_id"] = custom_id             # routed (and delivered) as the real id
     await next()

.. code-block:: toml

   # micro.toml: run that router instead of the stock one
   [processes.interactions]
   components = ["myapp.router:router", "micro.discord.interactions:CommandSync"]

.. code-block:: python

   # myapp/ids.py: import this once in every process that sends components
   from micro.discord.ui import hooks

   from .signing import sign

   @hooks.serialize
   def sign_custom_ids(component, next):
     data = next()
     if "custom_id" in data:                    # buttons, selects, modals, uploads...
       data["custom_id"] = sign(data["custom_id"])
     return data

That is a *serialize hook* (:doc:`ui`): it runs whenever any component becomes JSON, so no
call site changes. Services keep writing the plain id, and the handlers keep matching it:

.. code-block:: python

   await ctx.respond("Close it?", components=[
     Button("Close", custom_id=CLOSE.encode(Ticket(id=42))),     # sent as ...~<mac>
   ])

   @components.match(CLOSE)                      # still matches plain "ticket.close:[42]"
   async def close(ctx: Interaction, ticket: Ticket) -> None: ...

Notes: the signature counts toward Discord's 100-character limit (``CustomId.encode`` checks
its own part, so leave room); every component and modal you send must then be signed (the hook does it, but a plain
dict component bypasses hooks and would be refused); commands and autocomplete have no ``custom_id`` and pass
straight through; and the secret must be the same in every process that signs or checks.

Deferring
---------

:func:`defers` is a ready-made middleware that acknowledges the interaction before the
handler runs, so slow work never hits Discord's three seconds. ``defers(thinking=False,
ephemeral=False)`` takes the same options as ``ctx.defer`` (a command always shows
"thinking..."; ``ephemeral=True`` makes the eventual answer private) and skips
autocomplete, which cannot be deferred.

Errors
------

An error anywhere (middleware, a custom ID that will not decode, a handler) is logged and
the user sees one ephemeral "Something went wrong." (or "This command was just updated" for
:class:`CommandOutdated`). To say something else, wrap ``next()`` in ``try/except`` in your
own middleware. A flow that ends without responding is logged as a warning; Discord will
show the user a failure.

Reference
---------

.. api::
   micro.discord.interactions.Flow
   micro.discord.interactions.defers
   micro.discord.interactions.MiddlewareError
   micro.discord.interactions.Middleware
   micro.middleware.Middlewares
   micro.middleware.Scoped
   micro.middleware.in_scope
