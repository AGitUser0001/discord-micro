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

``InteractionRouter.use`` runs **before routing**, and may change the payload. That is how
you unwrap a signed or encrypted custom ID so it routes by its real prefix:

.. code-block:: python

   @router.use
   async def unwrap(ctx, next, end):
     data = ctx.payload.get("data") or {}
     if "custom_id" in data:
       data["custom_id"] = codec.decode(data["custom_id"])   # routes by the real prefix
     await next()

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
