Discord state
=============

How it works, in four steps
---------------------------

1. Discord sends **events** (a role was edited, a member left, a channel was created) to your
   bot's shards. Discord gives each server to exactly **one** shard,
   ``(guild_id >> 22) % shard_count``, so one connection sees everything that happens in it.
2. Each Gateway worker folds the events of its connections into **memory**: for every server it
   serves, the roles, channels, members and the rest. Nothing is stored, and no extra service
   is needed. A connection that starts or reconnects from scratch is handed every server again
   (``GUILD_CREATE``), so there is nothing to recover.
3. Your code asks :class:`DiscordState`, which **asks the connection that holds the answer**
   over NATS. If it has it you get it; if not you get ``None``. It never calls Discord, so
   what to do about a miss is your decision.
4. Anything that is not about one server (a user, or a role or channel found by id alone) is
   asked of **every shard at once**. Whichever shards know it answer, and the newest copy
   wins. A shard that is down simply does not contribute.

Who is who
----------

.. code-block:: text

   Discord ──events──▶ GatewayWorker      one connection per shard; it keeps that shard's
                                          servers in memory (the guilds, and the users it
                                          has seen)
                              ▲
                              │  a question over NATS, to the shard (or to all shards)
                              │
                       DiscordState       not a service: a small client class you create in
                                          any process (``DiscordState(runtime)``)

There is nothing to run besides the workers you already have; there is no ``Store`` and no
projection service. Every process can have its own ``DiscordState``, and they all get the
same answers.

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

Every read returns a typed view (:doc:`objects`) or ``None``. ``None`` means **state does not
know**, which is not the same as "it does not exist". `DiscordState` never asks Discord:
whether to fetch what is missing through the :doc:`api`, or to treat it as absent, is for the
caller to decide:

.. code-block:: python

   member = await state.member(guild_id, user_id)
   if member is None:
     member = (await api.guild(guild_id).member(user_id).get()).unwrap()

``permissions`` computes a member's effective permissions (roles, administrator, owner,
then the channel's overwrites) from those reads and gives ``None`` unless it has all of
them; :func:`compute_permissions` is the pure function if you already hold the data.

Users, members and guilds
-------------------------

A **user** is global: the same person in every server. A **member** is that user in one
server (roles, nickname, join date), kept separately for each, and it links back to its user
(``member.user``). Many events carry a user (a member joining or updating, a message, a
reaction, typing, a voice change, a ban, an invite, a presence update, ``USER_UPDATE``, the
member list), and each one keeps it current. Each shard stamps the users it hears of, so
``state.user`` asks every shard and keeps the newest.

You can walk from a user to the servers it is in, and from each to the user as a member:

.. code-block:: python

   user = await state.user(user_id)                   # the same in every server, or None
   for known in await state.mutual_guilds(user_id):   # a KnownGuild for each it is in
     member = await known.member()                    # the user there

``mutual_guilds`` is what the shards **know**, like discord.py's ``User.mutual_guilds``, which
is also computed from its cache. Discord has no such field for bots, so the name is only
borrowed: this is not Discord's complete list. It covers the members the shards have seen, so
a server whose member list was never received (no ``guild_members`` intent) only appears once
the user has done something in it. If the shard of a server is down, that server is missing
from the answer.

What a miss means
-----------------

* A **guild that is not held** (its shard is down, reconnecting, or has not yet been sent the
  server) answers nothing: every read of it is ``None``. A server in a Discord outage
  (``GUILD_DELETE`` with ``unavailable``) is kept but not served until it is back.
* A list (``roles``, ``channels``) is only given once the guild's **full state** has been
  received (its ``GUILD_CREATE``), so it is complete, not just what events happened to carry.
* **Members** are known only to the extent events and the member list have delivered
  them. With the ``guild_members`` intent each connection asks Discord for every member of
  every guild once, when it connects and when the bot joins a guild. Joins, updates and
  leaves keep them current after that. Without the intent, only members that events carry
  (people who speak, join, or are mentioned) are held.
* A **user** nothing has seen is ``None``.

Turn the members intent on to get the member list:

.. code-block:: python

   await GatewayControl(runtime).configure(intents="unprivileged,guild_members")
   # or: micro configure, open "gateway", and change intents

Only the state of a guild is kept (guilds, channels, threads, roles, members, emojis, voice
states, presences, stage instances, stickers, scheduled events). Messages, reactions, typing
and the like are events, not state, and are not kept.

How it stays right
------------------

* A ``GUILD_CREATE`` is the guild's whole state: it **replaces** what was held for the
  guild, so anything it no longer lists is removed. The exception is members: it lists only
  some, and the member list follows, so (with the members intent) members stay readable
  through a reconnect, and when the list is complete whoever it does not list is removed.
  Every other dispatch changes the objects it names (a role edit, a channel deletion, a
  member leaving) and nothing else. A guild that is removed from (``GUILD_DELETE``) is
  dropped.
* A connection that is not READY answers ``None`` for everything: what it holds may be
  behind. A resume replays what was missed, so it answers again; a new session starts empty
  and is sent every server again. A shard that is only waiting to take over (while a roll
  hands it over, or a new generation warms up) folds events too, and answers once it owns
  the shard, so a handover has nothing to catch up.
* Reads are answered by memory, so they cost one NATS round trip to the worker that owns
  the shard, and a worker that has not got the shard simply is not asked.

Reference
---------

.. api::
   micro.discord.state.DiscordState
   micro.discord.state.KnownGuild
   micro.discord.state.compute_permissions
   micro.discord.state.ALL_PERMISSIONS
