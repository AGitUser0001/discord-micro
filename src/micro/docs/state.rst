Discord state
=============

A guild's roles, channels, members and the rest reach you spread over shards and
connections that come and go. Gateway workers keep **nothing of their own**, which is what
lets any number of them run and be replaced. Instead Micro **aggregates** what every shard
sees into one view of Discord, in the :doc:`store`, organised by guild whichever shard or
connection delivered it, and you read that view from anywhere with :class:`DiscordState`.

.. code-block:: python

   from micro.discord.state import DiscordState

   state = DiscordState(runtime)
   role = await state.role(role_id)                  # by id alone
   channel = await state.channel(channel_id)         # it knows its guild
   roles = await state.roles(guild_id)               # every role of a guild
   channels = await state.channels(guild_id)
   guild = await state.guild(guild_id)
   member = await state.member(guild_id, user_id)
   allowed = await state.permissions(guild_id, user_id, channel_id)

Every read returns a typed view (:doc:`objects`) or ``None``. ``None`` means **the
aggregation does not hold it**, which is not the same as "it does not exist". `DiscordState`
never asks Discord: whether to fetch what is missing through the :doc:`api`, or to treat it
as absent, is for the caller to decide:

.. code-block:: python

   member = await state.member(guild_id, user_id)
   if member is None:
     member = (await api.guild(guild_id).member(user_id).get()).unwrap()

If the store is not running, that is an error (:class:`RoutingError`), not a miss.

``permissions`` computes a member's effective permissions (roles, administrator, owner,
then the channel's overwrites) from those reads and gives ``None`` unless it has all of
them; :func:`compute_permissions` is the pure function if you already hold the data.

What a miss means
-----------------

* A **guild that is not current** holds nothing until it is: while the connection that
  delivered it has a gap (see below), every read of it is ``None``.
* A list (``roles``, ``channels``) is only given once the guild's **full state** has been
  received (its ``GUILD_CREATE``), so it is complete, not just what events happened to carry.
* **Members** are known only to the extent events and the member list have delivered
  them. With the ``guild_members`` intent each connection asks Discord for every member of
  every guild once, when it connects and when the bot joins a guild. Joins, updates and
  leaves keep them current after that. Without the intent, only members that events carry
  (people who speak, join, or are mentioned) are held.
* A user is a different member in each guild, and the aggregation keeps them apart.

Running it
----------

A :class:`GatewayProjection` service consumes every connection's dispatches and folds
them into a store, in event order.

.. code-block:: toml

   [processes.state]
   components = ["micro.store:Store", "micro.gateway.projection:GatewayProjection"]

.. code-block:: python

   await GatewayControl(runtime).configure(intents="unprivileged,guild_members")
   # or: micro configure, open "gateway", and change intents

Run **one** projection replica: it applies events in order. Only the state of a guild is
kept (guilds, channels, threads, roles, members, emojis, voice states, presences, stage
instances, stickers, scheduled events). Messages, reactions, typing and the like are events,
not state, and are not stored.

How it stays right
------------------

* A ``GUILD_CREATE`` is the guild's whole state: it **replaces** what was held for the
  guild, so anything it no longer lists is removed. Every other dispatch changes the objects
  it names (a role edit, a channel deletion, a member leaving) and nothing else. A guild
  that is removed from (``GUILD_DELETE``) is dropped; one that is merely *unavailable*
  during an outage is kept but not current.
* Which shard or connection delivered a guild does not matter to a reader. It matters to
  freshness only: a guild is **current** unless the connection that last delivered it has a
  gap. A connection that disconnects marks its guilds not current; a **resume**, which
  replays what was missed, makes them current again; a connection that is lost for good
  leaves them not current until a new connection's ``GUILD_CREATE`` replaces them.
  A reconnect therefore cannot leave you reading data from before a gap, and a new
  generation (:doc:`gateway`) syncs the guilds in place without emptying the view.

What is stored
~~~~~~~~~~~~~~

The projection's own schema (``GATEWAY_PROJECTION``) has a ``GatewayGuild`` per guild
(which connection delivered it, whether it is current, whether its full state was
received), a ``DiscordObject`` per held object (``guildId``, ``kind``, ``id``, ``payload``),
a ``DiscordIndex`` that finds a channel or role from its id alone, and a ``GatewayConnection``
that remembers which guilds it delivered. Members and presences are keyed ``<guild>:<user>``.
You can query it with ``StoreClient`` like any other module.

Reference
---------

.. api::
   micro.discord.state.DiscordState
   micro.discord.state.compute_permissions
   micro.discord.state.ALL_PERMISSIONS
   micro.gateway.projection.GatewayProjection
   micro.gateway.projection.ProjectedObject
