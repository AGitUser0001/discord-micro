Interaction router
==================

:class:`InteractionRouter` is the one component that sees **every** interaction and decides
which service queue it goes to. Run it once per deployment, with any number of replicas.

It listens for the raw ``INTERACTION_CREATE`` dispatch (from the :doc:`gateway` or the
:doc:`endpoint`) and for each one:

1. runs its middleware (``router.use``, :doc:`middleware`), which may change the payload;
2. computes the **route**: ``cmd.<type>.<name>`` for a command (or autocomplete),
   ``cmp.<prefix>`` for a component and ``mdl.<prefix>`` for a modal, where the prefix is the
   part of the custom ID before the first ``:`` (or a declared pattern's route, see
   :doc:`components`);
3. checks that something can take it (:meth:`InteractionRouter.owned`): a live service that
   declared the route in its presence entry, or else a worker currently waiting on the
   route's consumer;
4. publishes it to the ``MICRO_INTERACTIONS`` work queue on that route with a TTL of
   Discord's three seconds, deduplicated by interaction ID.

Nothing can take it? :meth:`InteractionRouter.unroutable` answers on the spot, with an
ephemeral "This isn't available right now. Please try again in a moment." (an empty list for
autocomplete), so the user sees a message rather than a failure.

Queues
------

Each route has **one durable consumer**, named from the route, that every replica and version of every
service handling that route pulls from. Any number of services may share a route. Consumers
are created by the services when they start; the router only publishes.

Customizing
-----------

Subclass it and override ``route`` (choose a different route, for example per guild or for an
A/B test), ``owned`` or ``unroutable``:

.. code-block:: python

   class GuildRouter(InteractionRouter):
     def route(self, payload):
       return super().route(payload)

A custom template for a new kind of handler subclasses :class:`InteractionTemplate`
(``routes()`` and ``resolve(interaction)``), or implements ``start`` / ``stop`` / ``metadata`` from
scratch.

Reference
---------

.. api::
   micro.discord.interactions.InteractionRouter
   micro.discord.interactions.RAW_INTERACTION
