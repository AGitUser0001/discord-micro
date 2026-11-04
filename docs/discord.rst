Discord
=======

All Discord access goes through NATS: Gateway workers publish dispatches,
HTTP workers make API calls. The token comes from ``DISCORD_TOKEN`` and is
never stored in NATS; rotate it by rolling the processes.

HTTP workers and client
-----------------------

.. code-block:: python

   from micro.discord import DiscordHTTPClient, DiscordHTTPWorker

   worker = DiscordHTTPWorker()                  # run any number
   http = DiscordHTTPClient(runtime)

   message = await http.call(                    # plain JSON parts
     "create_message", path={"channel_id": "1"}, body={"content": "hi"}
   )
   result = await http.create_message(request)   # generated, typed method per operation

``call`` raises ``DiscordAPIError`` (``status``, ``body``) for error statuses.
Requests are routed by rendezvous hashing over live workers on Discord's major
parameters, so a rate-limit bucket's requests share one worker; buckets live
in memory, global 429s are broadcast to every worker, and only a departed
worker's partitions move.

Gateway workers
---------------

.. code-block:: python

   from micro.gateway import GatewayWorker

   GatewayWorker(intents=hikari.Intents.ALL_UNPRIVILEGED, shard_count=1, max_concurrency=1)

Workers balance shards through TTL leases, reclaim a crashed worker's shards,
hand shards over without gaps when draining, and respect identify concurrency.
Only the owner of a shard publishes its dispatches.

.. code-block:: python

   from micro.gateway import ActivityUpdate, GatewayControl

   control = GatewayControl(runtime)
   await control.update_presence(status="idle", activity=ActivityUpdate(name="maintenance"))
   await control.request_guild_members(guild_id, query="", limit=0)
   await control.update_voice_state(guild_id, channel_id)
   await control.set_shard_count(4)   # rolls in a new generation, then flips publishing
   await control.roll()               # new generation, same size
   status = await control.status()

Dispatch events
---------------

Typed schemas for every dispatch, created on first use:

.. code-block:: python

   from micro.schemas import events

   @service.listen(events.MESSAGE_CREATE)
   async def on_message(message: GatewayMessageCreateDispatchData) -> None: ...

Filters
-------

.. code-block:: python

   from micro.discord.filters import all_of, any_of, content_startswith, from_users, ignore_bots, in_channel, in_guild, not_from

   @service.listen(events.MESSAGE_CREATE, when=all_of(ignore_bots, in_channel(123), content_startswith("!")))
   async def command(message) -> None: ...

Messages and UI
---------------

Mentions never ping unless allowed.

.. code-block:: python

   from micro.discord.messages import reply_to, send
   from micro.discord.ui import ActionRow, AllowedMentions, Button, Select, SelectOption, embed

   await send(http, channel_id, "Hi <@1>", allowed_mentions=AllowedMentions.only(users=[1]))
   await reply_to(http, message, embeds=[embed("Title", "Body", fields=[("a", "b", True)])],
                  components=[Button("Open", custom_id="ticket.open"), Button("Docs", url="https://...")])

Loose buttons fill rows of five; selects get their own row.

State
-----

.. code-block:: python

   from micro.discord.state import DiscordState

   state = DiscordState(runtime)
   guild = await state.guild(guild_id)          # StateRead(value, source)
   member = await state.member(guild_id, user_id)
   roles = await state.roles(guild_id)
   channel = await state.channel(channel_id, guild_id=guild_id)
   perms = await state.permissions(guild_id, user_id, channel_id)

Reads use the store projection when it runs and the guild's connection is
live, otherwise Discord's API; ``source`` says which. Values are typed views
(``Guild``, ``Member``, ``Role``, ``Channel``, ``User``, ``Message``) that keep
unknown fields.

Generated models
----------------

``micro.discord.models.{gateway,http,http_requests}`` cover Discord's whole API.
They are split per definition and imported lazily, so a process loads only the
models it touches.
