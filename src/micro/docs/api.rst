The Discord API
===============

``api`` has **one method for every Discord operation**: all 242, generated from Discord's
own OpenAPI specification, so names, arguments and types match Discord's documentation.
You get it as ``ctx.api`` in an interaction handler or ``DiscordHTTPClient(runtime).api``
anywhere else. Every call goes through the :doc:`http-worker`, so rate limits, retries and
the token are handled for you.

.. code-block:: python

   api = ctx.api
   sent = await api.create_message(channel_id, Draft("hi", embeds=[Embed("T", "D")]))
   message = sent.unwrap()                                   # or match on Ok / Err
   await api.update_message(channel_id, message.id, "edited")
   await api.create_message(channel_id, Draft("see attached", files=[Upload("report.pdf", data)]))
   await api.ban_user_from_guild(guild_id, user_id, delete_message_seconds=3600, reason="spam")
   await api.update_channel(channel_id, topic=None)          # None is sent as null

Results
-------

**Every method returns a** :class:`Result`: an :class:`Ok` with the typed value, or an
:class:`Err` with the :class:`DiscordAPIError` when Discord answered with an error status.
Discord saying no (missing permission, the thing is gone, DMs closed) is an ordinary outcome
of a working bot, not an exception, so you handle it where it matters:

.. code-block:: python

   match await api.message(channel_id, message_id).delete():
     case Ok(): ...
     case Err(NotFound()): ...                  # already gone
     case Err(Forbidden() as error): print(error.code, error.message)
     case Err(error): raise error

   message = (await api.get_message(channel_id, message_id)).unwrap()   # abort: raises
   maybe = (await api.get_message(channel_id, message_id)).ok()         # or None

``unwrap()`` raises the original error, so a generic handler sees what it always did. What
is **not** a result stays an exception: a wrong argument (``ValidationError``), no worker
running (``RoutingError``), NATS down. See :doc:`errors`.

Arguments
---------

* **Path ids are positional**, in the order of Discord's path: ``api.get_guild_member(guild_id,
  user_id)``. Ids may be ints or strings at any depth; Micro turns them into the strings
  Discord expects.
* **Everything else is a keyword**, with the types Discord's models give them. A request
  body's fields and query parameters are all keywords. The exception is a message: every
  operation that sends or edits one takes it as a :class:`Draft` (or a string for text only)
  in place of ``content``, ``embeds``, ``components``, ``allowed_mentions``, ``flags``,
  ``tts``, ``message_reference`` and ``attachments``, the second positional argument.
* **Leaving an argument out leaves it out of the request. Passing ``None`` sends ``null``**,
  which is how you clear a field (a topic, a nickname).
* A mistake (a wrong type, an unknown field, a value outside Discord's limits) is a
  ``pydantic.ValidationError`` raised **before anything is sent**.
* Files go in the ``Draft`` of a message operation; the few operations that take one file
  (stickers, some invite operations) use ``file=Upload(...)``.
* ``reason="..."`` on every operation that changes something becomes the audit log reason.
* Micro's builders go wherever Discord wants JSON: components (loose buttons are laid into
  rows; layout components set the v2 flag), embeds, :class:`AllowedMentions` (see :doc:`ui`).
  **A message mentions nobody unless you allow it.**

What comes back
---------------

The typed response model (with every field Discord sent), a list of them, or ``None`` for an
operation that returns nothing. A Discord error status raises :class:`DiscordAPIError`
(``status``, ``body``). An operation Micro has no model for yet falls back to the decoded
JSON.

Refs
----

A **ref** is an object by id with its ids filled in, plus the handful of operations you use
most on it. Nothing is fetched until you call a method.

.. code-block:: python

   channel = api.channel(5)
   await channel.send("hello", components=[...])
   await channel.message(9).reply("yes")                   # same as api.message(5, 9)
   await channel.message(9).react("👍")                    # or Emoji("wave", 123)
   thread = await channel.message(9).start_thread(name="discuss")

   member = api.guild(7).member(8)                         # same as api.member(7, 8)
   await member.timeout(datetime(2030, 1, 1, tzinfo=UTC), reason="cool off")
   await member.add_role(20)
   await api.guild(7).ban(8, reason="spam")
   await api.user(8).send("hello")                         # opens the DM first

There are refs for channels, messages, guilds, members, roles, users, emojis, stickers,
scheduled events, webhooks (``webhook(id)`` and ``webhook_token(id, token)``), invites and
application commands: 156 methods in all, listed below. Everything else is on ``ref.api``.
In an interaction handler, ``ctx.channel_ref``, ``ctx.guild_ref``, ``ctx.member_ref``,
``ctx.user_ref`` and ``ctx.message_ref`` are that interaction's own.

Objects and ``.full()``
-----------------------

Events, interactions and some API results give you light **views** (``User``, ``Member``,
``Role``, ``Channel``, ``Guild``, ``Attachment``, ``Message``, :doc:`objects`) that type a
few fields but keep every other one Discord sent (``message.pinned``,
``user.banner``). A field Discord spells ``color`` is ``colour`` here, as a :class:`Colour`
(``role.colour``, ``user.accent_colour``). ``.full()`` converts one to Discord's full generated model.

Generated models
----------------

``micro.discord.models.{gateway,http,http_requests}`` cover Discord's whole API. They are
split per definition and imported lazily, so a process loads only the models it touches.
``HTTP_OPERATIONS`` maps each operation id to its method, path, request model, content types
and path fields (:class:`DiscordHTTPOperation`).

Reference
---------

.. api::
   micro.discord.api.Upload
   micro.discord.refs.ChannelRef
   micro.discord.refs.MessageRef
   micro.discord.refs.GuildRef
   micro.discord.refs.MemberRef
   micro.discord.refs.RoleRef
   micro.discord.refs.UserRef
   micro.discord.refs.EmojiRef
   micro.discord.refs.StickerRef
   micro.discord.refs.ScheduledEventRef
   micro.discord.refs.WebhookRef
   micro.discord.refs.WebhookTokenRef
   micro.discord.refs.InviteRef
   micro.discord.refs.CommandRef
   micro.discord.api.DiscordAPI brief
