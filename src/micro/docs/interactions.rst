Interactions
============

An **interaction** is what Discord sends when someone uses a slash command, a context-menu
command, a button, a select menu, a modal, or autocomplete. You have three seconds to
answer the first time. Micro turns each interaction into a message on a work queue, one
queue per route, so the right service handles it no matter which process received it.

.. code-block:: text

   Discord ──► GatewayWorker ─┐
                              ├─► InteractionRouter ─► route queue (3 s TTL)
   Discord ──► InteractionEndpoint ┘                        │
                                      Commands / Components / Modals / RuntimeCommands
                                      on any service ─► Interaction (interaction) ─► HTTP worker

What each part is for
---------------------

.. list-table::
   :header-rows: 1
   :widths: 28 72

   * - Part
     - Role
   * - :doc:`commands`
     - ``Commands``: slash, user and message commands from typed Python functions.
   * - :doc:`components`
     - ``Components`` and ``Modals``: buttons, selects and modals, matched by custom ID
       (``CustomId`` carries typed state).
   * - :doc:`responding`
     - ``Interaction`` (``interaction``): respond, defer, edit, follow up, modal, autocomplete, and
       read what was submitted.
   * - :doc:`middleware`
     - ``use``: authorization, deferral, logging and error replies around every handler.
   * - :doc:`runtime-commands`
     - ``RuntimeCommands``: commands created and removed while the bot runs.
   * - :doc:`router`
     - ``InteractionRouter``: picks the route and queue of each interaction.
   * - :doc:`command-sync`
     - ``CommandSync``: registers your commands with Discord safely across rollouts.
   * - :doc:`endpoint`
     - ``InteractionEndpoint``: receive interactions over HTTP instead of the Gateway.

A minimal bot
-------------

.. code-block:: python

   from micro.discord.interactions import Commands, Interaction
   from micro.service import Service

   service = Service("hello")
   commands = Commands(service)

   @commands.slash("hello", description="Say hello")
   async def hello(ctx: Context, interaction: Interaction, name: str = "world") -> None:
     await interaction.respond(f"Hello, {name}!")

and in ``micro.toml``, once per deployment:

.. code-block:: toml

   [processes.interactions]
   components = [
     "micro.discord.interactions:InteractionRouter",
     "micro.discord.interactions:CommandSync",
   ]

Both run with any number of replicas. The router is what turns raw interactions into queue
items; ``CommandSync`` is what makes ``/hello`` appear in Discord.

Guarantees
----------

* **At most once, never late.** A route queue holds an interaction for Discord's three
  seconds (the queue's TTL), after which it is dropped rather than delivered stale. A
  handler that fails does not get it redelivered (an interaction can be answered only once).
* **Shared by every replica and version.** Each route has one durable consumer that every
  replica of every service handling it pulls from, so rolling deploys never drop or double
  an interaction.
* **Deduplicated** by interaction id, so a replayed Gateway event does not run twice.
* **Nothing handles it?** The router answers with an ephemeral "isn't available right now"
  so the user does not see a failure.
* **Timing is visible.** ``interaction.age`` is the seconds since Discord created the interaction.
  A handler that starts more than 2 s into Discord's 3 s logs a warning, and a failure logs
  its age, so an ``Unknown interaction`` error shows whether the time went before the
  handler (gateway, NATS, a skewed clock) or inside it.

Reference
---------

.. api::
   micro.discord.interactions.InteractionTemplate
   micro.discord.interactions.InteractionState
   micro.discord.interactions.ResponseType
   micro.discord.interactions.ensure_interactions_stream
   micro.discord.interactions.route_consumer
   micro.discord.interactions.INTERACTIONS_KEY
   micro.discord.interactions.RESPONSE_DEADLINE
   micro.discord.interactions.TOKEN_LIFETIME
   micro.discord.routes.route_token
   micro.discord.routes.command_route
   micro.discord.routes.component_route
   micro.discord.routes.modal_route
   micro.discord.routes.custom_id_prefix
   micro.discord.routes.interaction_route
   micro.discord.routes.interaction_subject
