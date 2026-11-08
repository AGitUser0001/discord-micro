Gateway workers
===============

A **gateway worker** keeps websocket connections to Discord and publishes every event it
receives onto NATS. Nothing else in Micro talks to the Gateway: services never hold a
connection, so you can restart, scale, or replace them without Discord noticing.

.. code-block:: text

   Discord ⇄ websocket ⇄ GatewayWorker ──► MICRO_EVENTS stream ──► your services
                              │                                  ├► InteractionRouter
                              ▼                                  └► GatewayProjection
                    leases, generations, locks (NATS KV)

:class:`GatewayWorker` is a plain component (see :doc:`runtime`). Start it from
``micro.toml`` or in code:

.. code-block:: toml

   [processes.gateway]
   components = ["micro.gateway:GatewayWorker"]
   replicas = 2

.. code-block:: python

   from micro.gateway import GatewayWorker

   await runtime.add(GatewayWorker(shard_count=4, max_concurrency=1))

Configuration
-------------

.. list-table::
   :header-rows: 1
   :widths: 20 22 58

   * - Argument
     - Environment
     - Meaning
   * - ``token``
     - ``DISCORD_TOKEN``
     - The bot token. Never written to NATS.
   * - ``shard_count``
     -
     - Shards when no generation exists yet (1 to 4096, default 1). After that,
       :class:`GatewayControl` decides.
   * - ``max_concurrency``
     -
     - Identifies Discord allows per 5 seconds (default 1; your bot's
       ``max_concurrency`` from Discord's gateway info).
   * - ``lease_ttl``
     -
     - Seconds a shard lease lives without renewal (at least 3, default 10).
   * - ``api_url``
     - ``DISCORD_API_URL``
     - Another API with Discord's shape, such as a fake for tests.
   * - ``networked``
     -
     - Follow the shared :class:`GatewaySettings` document (see below). Default false.
   * - ``name``
     -
     - Component name (default ``gateway``).

Run **as many workers as you like**. They divide the shards between themselves; with more
workers than shards the extras idle as spares.

Intents
-------

There is **one way** to set the Gateway intents: ``GatewayControl.set_intents`` (or the same
thing from the command line). There is no worker argument and no environment variable, so
there is never a second place that disagrees with the first.

.. code-block:: console

   micro gateway intents                                  # show what is in force
   micro gateway intents unprivileged,message_content     # set them

.. code-block:: python

   await GatewayControl(runtime).set_intents("unprivileged,message_content,guild_members")
   await GatewayControl(runtime).set_intents(0b1000000000000001)    # or a number

Names are hikari's intent names (``message_content``, ``guild_members``, ...), plus
``unprivileged``, ``privileged`` and ``all`` for hikari's groups, comma separated. A typo is
rejected with a suggestion before anything is written.

* Until you set them, workers connect with Discord's **unprivileged** set.
* They are stored in the Gateway **generation** (next to the shard count), so they persist
  across restarts of any process and of NATS, and every worker, including one that starts
  later, connects each generation with the intents recorded in it.
* Changing them is a **new generation**: it connects beside the old one and takes over only
  when every shard is READY. So intents Discord refuses (a privileged one not switched on in
  the developer portal) never take the bot offline: the old generation keeps serving, and
  setting the previous intents again replaces the stuck one. Resharding keeps them.
* It is idempotent: setting the intents already in force writes nothing.

Three intents need switching on under **Bot > Privileged Gateway Intents** in the developer
portal as well: ``message_content`` (message text, for ``!ping``-style commands),
``guild_members`` (the member list, :doc:`cache`) and ``guild_presences``.


How shards are shared
---------------------

Every shard is a **lease** in the ``micro_shards`` table with a time to live. A worker
claims its fair share, renews them while it lives, and takes over leases that expired
because their owner crashed. When a worker is told to drain (``Ctrl-C``, a rolling
update) it connects its shards on a standby connection of the next owner first, then
releases, so a shard changes hands without a gap in events. Identifies are spaced by
a gate in ``micro_locks`` so that all workers together respect Discord's
``max_concurrency``.

Only the **owner** of a shard publishes its dispatches. A connection that is not the
owner (a standby while handing over, or a new generation warming up) publishes the same
events to ``micro.discord.standby...``, which only :class:`GatewayProjection
<micro.gateway.projection.GatewayProjection>` reads.

Generations
~~~~~~~~~~~

Changing the shard count, or replacing every connection, is a **generation**. The new
generation is written with :class:`GatewayControl`; workers open it beside the old one,
and flip publishing to it once every new shard is READY. Until then the old generation
keeps serving, so reshard live:

.. code-block:: python

   from micro.gateway import ActivityUpdate, GatewayControl

   control = GatewayControl(runtime)
   await control.set_shard_count(4)     # new generation of 4 shards, flip when ready
   await control.roll()                 # new generation, same size
   status = await control.status()      # generations, shards, owners, who is ready

Networked settings
------------------

``GatewayWorker(networked=True)`` follows a shared :class:`GatewaySettings` document for
``max_concurrency`` and ``lease_ttl``, so they are changed once for every worker, with
``GatewayControl.configure(...)`` or ``micro configure gateway max_concurrency=2``. The token
and the NATS address stay in each process's environment (they are needed before NATS is
reachable); the worker's own arguments are its **bootstrap** values, used until the document
is loaded and to create it the first time. Intents are deliberately not in it (see above).
Details in :doc:`config`.

Controlling a live connection
-----------------------------

:class:`GatewayControl` is the client side. It needs only a runtime, so any service, script
or the :doc:`bridge` can use it.

.. code-block:: python

   await control.update_presence(status="idle", activity=ActivityUpdate(name="maintenance"))
   await control.request_guild_members(guild_id, query="", limit=0)   # members arrive as events
   await control.update_voice_state(guild_id, channel_id, self_mute=True)
   shard = await control.shard_for(guild_id)
   connection = await control.connection_for(guild_id)   # the READY connection id, or None

* ``update_presence`` writes the presence to a table that every worker watches, so it is
  applied to every shard now and to any that connect later. It is not tied to a guild.
* ``request_guild_members`` and ``update_voice_state`` go to the one worker that owns the
  shard of that guild (``(guild_id >> 22) % shard_count``). They raise ``RoutingError`` if
  no worker owns it right now and ``RequestTimeoutError`` if it does not answer.

What it publishes
-----------------

.. list-table::
   :header-rows: 1
   :widths: 45 55

   * - Subject
     - Meaning
   * - ``micro.discord.dispatch.<EVENT>.<guild or _>``
     - One Gateway dispatch, as Discord sent it.
   * - ``micro.discord.standby.<EVENT>.<guild or _>``
     - The same, from a connection that does not own the shard.
   * - ``micro.gateway.connection.<kind>``
     - Lifecycle: ready, connected, disconnected, resumed, invalidated.

Both go to the ``MICRO_EVENTS`` stream with ``Micro-Shard``, ``Micro-Generation`` and
``Micro-Connection`` headers. A connection id changes on every READY (a new session) and
stays across resumes, which is what lets the :doc:`cache` know when to start clean.
Use ``service.listen(...)`` rather than these subjects directly (see :doc:`events`).

When a connection gets READY and has the ``guild_members`` intent it asks Discord for the
full member list of each guild once, and again for a guild the bot joins later.

Reference
---------

.. api::
   micro.gateway.GatewayWorker
   micro.gateway.GatewayControl
   micro.gateway.GatewayStatus
   micro.gateway.GatewayGeneration
   micro.gateway.GatewaySettings
   micro.gateway.ShardLease
   micro.gateway.ActivityUpdate
   micro.gateway.PresenceUpdate
   micro.gateway.VoiceStateUpdate
   micro.gateway.GuildMembersRequest
   micro.gateway.ConnectionEvent
   micro.gateway.ConnectionEventKind
   micro.gateway.ShardHost
   micro.gateway.ShardSession
   micro.gateway.HikariShard
   micro.gateway.guild_of
   micro.gateway.lease_key
