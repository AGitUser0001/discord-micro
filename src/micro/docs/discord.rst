Discord
=======

All Discord access goes through NATS: Gateway workers publish dispatches,
HTTP workers make API calls. The token comes from ``DISCORD_TOKEN`` (set it in
``.env`` or the environment) and is never stored in NATS; rotate it by rolling the processes.
``DISCORD_API_URL`` (or ``api_url=`` on the HTTP and Gateway workers) points them
at another API with Discord's shape, such as a proxy or a fake for testing.

Invite links
------------

``micro invite`` prints the link that adds the bot to a server and the one that
installs its commands on a user's account. It reads the application ID from
``DISCORD_TOKEN`` (or ``DISCORD_APPLICATION_ID``) and the permissions from
micro.toml:

.. code-block:: toml

   [invite]
   permissions = ["view_channel", "send_messages", "embed_links"]   # names or numbers

.. code-block:: console

   micro invite                    # both links
   micro invite -p admin           # other permissions, once
   micro invite --guild 1234       # preselect (and lock) one server

Names are Discord's (``manage_roles``, ``Moderate Members``, ...); a typo is
caught with a suggestion, and also when ``micro dev`` loads micro.toml. Enable
*User Install* under Installation in the Developer Portal for the second link
to work. In code:

.. code-block:: python

   from micro.discord.invite import Permissions, invite_url

   invite_url("1234", permissions=Permissions.SEND_MESSAGES | Permissions.EMBED_LINKS)
   invite_url("1234", install="user")      # also: guild_id=, redirect_uri=, state=

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
   api = http.api                                # the same, with plain arguments (below)

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

Intents come from ``DISCORD_INTENTS`` (default ``unprivileged``): names or numbers,
comma separated. Reading message text (``!ping`` in the ``chat`` package) needs
the privileged ``message_content`` intent, switched on both here and under
**Bot > Privileged Gateway Intents** in the Discord developer portal:

.. code-block:: sh

   DISCORD_INTENTS=unprivileged,message_content

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

Doing anything: ``api`` and refs
--------------------------------

``http.api`` (``ctx.api`` in a handler) has **one method per Discord operation**, all
242, generated from Discord's own specification. Path ids are positional and the
rest are keywords, with the types Discord's models give them; a mistake is a
``ValidationError`` before anything is sent, and a failed call raises
``DiscordAPIError``. What comes back is the typed response (every field Discord
sent), a list of them, or ``None``.

.. code-block:: python

   api = ctx.api
   message = await api.create_message(channel_id, "hi", embeds=[embed("T", "D")])
   await api.update_message(channel_id, message.id, content="edited")
   await api.create_message(channel_id, "see attached",
                            files=[Upload("report.pdf", data)])
   await api.ban_user_from_guild(guild_id, user_id, delete_message_seconds=3600,
                                 reason="spam")         # reason= is the audit log
   await api.update_channel(channel_id, topic=None)      # None is sent as null

* Ids may be ints or strings, at any depth. Leaving an argument out leaves it out
  of the request; passing ``None`` sends ``null``, which is how you clear a field.
* Micro's builders go wherever Discord wants JSON: components (loose buttons are laid
  into rows; layout components set the v2 flag), ``AllowedMentions``, embeds. A
  message mentions nobody unless you allow it.
* ``files=[Upload(name, bytes, content_type=None)]`` on every operation that accepts
  uploads; the others (stickers, invite lists) take ``file=Upload(...)``.
* ``reason=`` on every operation that changes something.

**Refs** are objects by id with their ids filled in, and the handful of operations
you use most on them (nothing is fetched until you call):

.. code-block:: python

   channel = api.channel(5)
   await channel.send("hello", components=[...])
   await channel.message(9).reply("yes")                 # api.message(5, 9)
   await channel.message(9).react("👍")                  # or Emoji("wave", 123)
   thread = await channel.message(9).start_thread(name="discuss")

   member = api.guild(7).member(8)                       # api.member(7, 8)
   await member.timeout(datetime(2030, 1, 1, tzinfo=UTC), reason="cool off")
   await member.add_role(20)
   await api.guild(7).ban(8, reason="spam")
   await api.user(8).send("hello")                       # opens the DM first

Refs exist for channels, messages, guilds, members, roles, users, emojis, stickers,
scheduled events, webhooks (``webhook(id)`` and ``webhook_token(id, token)``),
invites and application commands: 156 methods in all (see ``micro.discord.refs``).
Everything else is on ``ref.api``. In an interaction handler, ``ctx.channel_ref``,
``ctx.guild_ref``, ``ctx.member_ref``, ``ctx.user_ref`` and ``ctx.message_ref`` are
this interaction's own.

**Everything Discord sent.** The ``User``, ``Member``, ``Role``, ``Channel``,
``Guild``, ``Attachment`` and ``Message`` views keep only a few typed fields but every
other one stays on the object (``message.pinned``, ``user.accent_color``), and
``.full()`` returns Discord's own typed model for it.

Watching requests
-----------------

Optional. A worker can call you back after every Discord request it makes, for
metrics or logging. A hook sees one worker's requests only (there is no shared
state), costs nothing when none is registered, and cannot break a request: its errors
are logged.

.. code-block:: python

   worker = DiscordHTTPWorker()
   remove = worker.hook(lambda e: print(e.operation, e.status, f"{e.seconds:.2f}s"))
   await runtime.add(worker)

The callback (sync or ``async``) gets an ``HTTPEvent``: ``operation``, ``route``,
``attempt`` (1 for the first try; a retry after a 429 is its own event), ``status``
(``None`` if no answer came back), ``seconds``, ``error`` and ``rate_limited``.
``remove()`` unhooks it.

Messages and UI
---------------

Mentions never ping unless allowed.

.. code-block:: python

   from micro.discord.messages import reply_to, send
   from micro.discord.ui import ActionRow, AllowedMentions, Button, Select, SelectOption, embed

   await send(http, channel_id, "Hi <@1>", allowed_mentions=AllowedMentions.only(users=[1]))
   await reply_to(http, message, embeds=[embed("Title", "Body", fields=[("a", "b", True)])],
                  components=[Button("Open", custom_id="ticket.open"), Button("Docs", url="https://...")])

Loose buttons fill rows of five; selects get their own row. See :doc:`interactions`
for every component.

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

Reads use the member and guild cache when it runs and the guild's connection is
live, otherwise Discord's API; ``source`` says which. Values are typed views
(``Guild``, ``Member``, ``Role``, ``Channel``, ``User``, ``Message``) that keep
unknown fields.

The cache
~~~~~~~~~

Gateway workers keep no cache of their own (that is what lets any number of them
run). The cache is shared instead: a ``GatewayProjection`` writes every worker's
dispatches (guilds, channels, roles, **members**, presences, voice states) into the
store, and ``DiscordState`` reads it from any service with no Discord request. A
member lookup that would cost a rate-limited REST call becomes a store read.

.. code-block:: toml

   [processes.cache]
   components = ["micro.store:Store", "micro.gateway.projection:GatewayProjection"]
   # and for the member list, in the environment:  DISCORD_INTENTS=unprivileged,guild_members

* With the ``guild_members`` intent (enable *Server Members Intent* in the developer
  portal) each connection asks Discord for **every member of every guild once**, when it
  connects and when the bot joins a new guild. Joins, updates and leaves keep the cache
  current after that. Without the intent only the members Discord sends in events
  (people who speak, join, or are mentioned) are cached.
* A user is a different member in each guild; the cache keeps them apart.
* A cache miss (someone not cached) is one REST call, shared by every concurrent
  lookup of the same member in that process.
* Run one projection replica: it applies events in order. The cache follows the
  connection: when the connection is lost its data is not served until it resumes,
  and a new connection starts clean, so the cache can never be stale across a
  reconnect.

Generated models
----------------

``micro.discord.models.{gateway,http,http_requests}`` cover Discord's whole API.
They are split per definition and imported lazily, so a process loads only the
models it touches.
