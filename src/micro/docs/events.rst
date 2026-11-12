Discord events
==============

Every Gateway dispatch (a message, a member joining, a reaction, a voice update) reaches
your services as an **event**. A service subscribes with ``listen``; the :doc:`gateway`
does the connecting. Nothing here depends on how many gateway workers or service replicas
run.

.. code-block:: python

   from micro.schemas import events
   from micro.service import Service

   service = Service("moderation")

   @service.listen(events.MESSAGE_CREATE)
   async def on_message(ctx: Context, message: Message) -> None:
     ...

``events.<NAME>`` is a :class:`DispatchSchema` for each of Discord's dispatches
(``MESSAGE_CREATE``, ``GUILD_MEMBER_ADD``, ``MESSAGE_REACTION_ADD``, ...), generated from
Discord's documentation and created the first time you touch it. Every event handler takes
the same two arguments, ``(ctx, event)``, and ``event`` is typed: for the events that are about one
object (a message, a member, a channel, a guild, a user) it is that object, already bound to
``ctx``; for the others it is Discord's generated model of the payload.

What a handler gets
-------------------

``ctx`` is the :class:`Context` (``ctx.api``, ``ctx.state``, ``ctx.store``, ...) and ``event`` is
the payload, as a bound object (:doc:`objects`) when the event is about one:

.. code-block:: python

   from micro.discord import Context, Member, Message

   @service.listen(events.MESSAGE_CREATE)
   async def ping(ctx: Context, message: Message) -> None:
     if message.content == "!ping":
       await message.reply("pong")

   @service.listen(events.GUILD_MEMBER_ADD)
   async def joined(ctx: Context, member: Member) -> None:
     channel = await ctx.state.channel(WELCOME_CHANNEL)
     if channel is not None:
       await channel.send(f"Welcome {member.mention}!")

``MESSAGE_CREATE`` and ``MESSAGE_UPDATE`` give a ``Message``; ``GUILD_MEMBER_ADD`` and
``GUILD_MEMBER_UPDATE`` a ``Member``; ``CHANNEL_*`` and ``THREAD_*`` a ``Channel``;
``GUILD_CREATE`` and ``GUILD_UPDATE`` a ``Guild``; ``USER_UPDATE`` a ``User``. Every other event
is Discord's generated model of its payload.

Before and after
~~~~~~~~~~~~~~~~

When an event **changes or removes** a member, channel, role, guild, voice state or presence the
shard held, the object as it *was* travels with it, and the handler reads it from ``event.before``:

.. code-block:: python

   @service.listen(events.GUILD_MEMBER_UPDATE)
   async def changed(ctx: Context, member: Member) -> None:
     if member.before is not None and member.before.roles != member.roles:
       ...                                   # their roles changed

``before`` is ``None`` when the event did not change a held object, or the shard had not seen
it yet.

When an event does not match its schema
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Events are validated strictly. One that does not fit its model is **not delivered**: it is
logged as an error naming the event and the field, and dropped (while replicas run
different versions of a schema it is left for a replica that can read it). The models are
generated from Discord's published types, so if Discord sends something they do not
describe, that log line is the cue to regenerate or correct the model.

Delivery
--------

* Every listening **service** gets each event once; the work is load-balanced across that
  service's replicas.
* Delivery is **at least once**: a handler that raises (or a replica that dies mid-event)
  has the event redelivered, and only the handlers that failed run again.
* A service with several ``listen`` handlers for one event runs them all.
* Events live in the ``MICRO_EVENTS`` stream, which keeps an event only while some
  service's durable consumer still has to see it (interest retention). So a service that
  restarts, or is rolled, **catches up** on what it missed; a service seen for the first
  time starts from "now"; an event nobody has ever subscribed to is dropped.

Narrowing what you receive
--------------------------

``guild_id=`` filters in NATS itself, so other guilds' events are never delivered to you:

.. code-block:: python

   @service.listen(events.MESSAGE_CREATE, guild_id=1234)
   async def only_this_guild(ctx: Context, message: Message) -> None: ...

``when=`` filters in your process, with a predicate that sees the payload. The helpers in
``micro.discord.filters`` read both dicts and models, and combine:

.. code-block:: python

   from micro.discord.filters import (
     all_of, any_of, content_startswith, from_users, ignore_bots, in_channel, in_guild, not_from
   )

   @service.listen(
     events.MESSAGE_CREATE,
     when=all_of(ignore_bots, in_channel(123), content_startswith("!")),
   )
   async def command(ctx: Context, message: Message) -> None: ...

``ignore_bots`` skips events authored by any bot, including yours. ``not_from(bot_id)``
skips only given users. Write your own as any ``Callable[[payload], bool]``.

Ordering
~~~~~~~~

Discord sends one guild's events in order, but replicas and retries do not preserve it.
``Service("x", ordered_by_guild=True)`` runs one guild's events one at a time, in order,
within each replica.

Replying to an event
--------------------

Send through the API like anywhere else (:doc:`api`); a ``Draft`` carries the reply, with
safe mention defaults:

.. code-block:: python

   from micro.discord import DiscordHTTPClient
   from micro.discord.ui import AllowedMentions, Draft

   api = DiscordHTTPClient(service.runtime).api
   (await api.channel(message.channel_id).send(Draft("pong", reply_to=message.id))).unwrap()

Reference
---------

.. api::
   micro.service.DispatchSchema
   micro.discord.filters.all_of
   micro.discord.filters.any_of
   micro.discord.filters.author
   micro.discord.filters.content_startswith
   micro.discord.filters.from_users
   micro.discord.filters.ignore_bots
   micro.discord.filters.in_channel
   micro.discord.filters.in_guild
   micro.discord.filters.not_from
   micro.discord.filters.Predicate
