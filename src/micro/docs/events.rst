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
   async def on_message(message) -> None:
     ...

``events.<NAME>`` is a :class:`DispatchSchema` for each of Discord's dispatches
(``MESSAGE_CREATE``, ``GUILD_MEMBER_ADD``, ``MESSAGE_REACTION_ADD``, ...), generated from
Discord's documentation and created the first time you touch it. The handler receives the
event as the schema's typed model, or as a plain dict if you annotate it that way.

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
   async def only_this_guild(message) -> None: ...

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
   async def command(message) -> None: ...

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
