Cache and state
===============

Gateway workers keep **no cache of their own**; that is what lets any number of them run
and be replaced. Micro keeps one shared cache instead, in the :doc:`store`, and reads it
from anywhere with :class:`DiscordState`.

.. code-block:: python

   from micro.discord.state import DiscordState

   state = DiscordState(runtime)
   guild = await state.guild(guild_id)             # StateRead(value, source)
   member = await state.member(guild_id, user_id)
   roles = await state.roles(guild_id)
   channel = await state.channel(channel_id, guild_id=guild_id)
   perms = await state.permissions(guild_id, user_id, channel_id)   # permission bits

Every read returns a :class:`StateRead` with the typed ``value`` (a ``Guild``, ``Member``,
``Role`` or ``Channel`` view, see :doc:`objects`) and a ``source``: ``"projection"`` if the
cache answered, ``"http"`` if it had to ask Discord. The cache answers when it is running
**and** the connection that owns the guild's shard is live; otherwise the same call quietly
falls back to the REST API, so your code works with or without it.

``permissions`` computes Discord's effective permission bits for a member (roles,
administrator, owner, then the channel's overwrites) from those reads;
:func:`compute_permissions` is the pure function if you already hold the data.

Running the cache
-----------------

A :class:`GatewayProjection` service consumes every connection's dispatches and writes
guilds, channels, roles, members, presences and voice states into a store, in event order.

.. code-block:: toml

   [processes.cache]
   components = ["micro.store:Store", "micro.gateway.projection:GatewayProjection"]

.. code-block:: python

   await GatewayControl(runtime).configure(intents="unprivileged,guild_members")
   # or: micro configure, open "gateway", and change intents

* Run **one** projection replica: it applies events in order.
* With the ``guild_members`` intent (switch on *Server Members Intent* in the developer
  portal) each connection asks Discord for **every member of every guild once**, when it
  connects and when the bot joins a new guild. Joins, updates and leaves keep the cache
  current after that. Without the intent, only members that events carry (people who speak,
  join, or are mentioned) are cached.
* A user is a different member in each guild, and the cache keeps them apart.
* A member who is **not** cached costs one REST call, and concurrent lookups of the same
  member in a process share it.

Why it cannot go stale
----------------------

Cache rows belong to a *connection*. A connection id changes on every READY and survives
resumes. When a connection is lost, its rows are not served until it resumes; when it
is replaced, its rows are deleted and the new connection fills its own. A projection
that starts late adopts the connections it sees dispatches from. Because rows follow the
connection, a reconnect can never leave you reading data from before a gap.

What is stored
~~~~~~~~~~~~~~

The projection's own schema (``GATEWAY_PROJECTION``) has a ``GatewayConnection`` entity
and a ``DiscordObject`` entity (``connectionId``, ``kind``, ``id``, ``guildId``, ``payload``).
Members and presences are keyed ``<guild>:<user>``. You can query it with
``StoreClient`` like any other module, for example ``discordObject(connectionId:,
kind:, id:)`` to read only objects of a live connection.

Reference
---------

.. api::
   micro.discord.state.DiscordState
   micro.discord.state.StateRead
   micro.discord.state.compute_permissions
   micro.gateway.projection.GatewayProjection
   micro.gateway.projection.ProjectedObject
