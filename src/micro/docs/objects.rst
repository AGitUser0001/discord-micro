Objects
=======

``micro.discord.objects`` holds the typed **views** Micro hands you for Discord objects.
They are Pydantic models that type the fields you reach for and **keep everything else**
Discord sent, so nothing is lost and nothing breaks when Discord adds a field.

.. code-block:: python

   message.content            # typed
   message.pinned             # not declared, but kept: still readable
   message.model_extra        # all the undeclared fields
   full = message.full()      # Discord's own generated model (MessageResponse)

``full()`` validates the data against Discord's generated response model for that object,
which is stricter and complete (``UserResponse``, ``GuildMemberResponse``, ``GuildRoleResponse``,
``GetChannelResponse200``, ``GuildResponse``, ``MessageAttachmentResponse``, ``MessageResponse``).
Use it when you want every field typed; use the view when you just need a few.

``Object`` is the root of every view that has an id (``User``, ``Role``, ``Channel``,
``Guild``, ``Attachment``, ``Message``): ``id``, ``snowflake`` (the id as a number),
``created_at`` (read from the id), and equality by kind and id. ``isinstance(x, Object)``
says "Discord gave this an id".

Where views come from
---------------------

* event payloads (``MESSAGE_CREATE`` is a ``Message``), and ``interaction.user``, ``interaction.member``, ``interaction.message``;
* command options (``user: User``, ``role: Role``, ``channel: Channel``, ``file: Attachment``);
* ``DiscordState`` reads (:doc:`state`);
* resolved entities of a component or modal (``interaction.submitted.users()``, ``interaction.submitted.roles(...)``, see
  :doc:`responding`).

``User.display_name`` is the global name, or the username without one; ``mention`` on a
``User`` or ``Member`` is the ``<@id>`` form. ``Member.id`` is its user's id (``None`` if
Discord sent no user). The views are **frozen**: read them, do not assign to them.

Kinds Discord numbers are enums (see the reference below): ``channel.type is
ChannelType.GUILD_VOICE``, ``overwrite.type is OverwriteType.ROLE``. They are ``IntEnum``\ s, so
they equal the numbers on the wire. A number Discord adds later is kept as a member named
``UNKNOWN_<n>`` instead of failing the read.

``full()`` raises ``ValidationError`` when the payload was partial: a member resolved from
an interaction, for instance, has no ``user`` of its own.

A :class:`Member` is a user **in one guild**, so its identity is the pair: ``member.guild_id``
and ``member.user`` (``member.id`` is the user's id). Two members are equal when both match.
Discord leaves both out of the members it nests in a guild or an interaction, so Micro fills
them in; when you build one from a payload yourself, pass both, or validation fails. A member's
own ``avatar`` (the picture set for that guild) is an Asset like the user's, and
``member.display_avatar`` is that or the user's.

Pictures are :class:`Asset` objects, not hashes: ``user.avatar`` is the avatar the user set
(or ``None``), ``user.display_avatar`` falls back to the default one Discord shows, and
``guild.icon`` is the server's icon or ``None``. An ``Asset`` has ``.url``, ``.animated``,
``with_size(256)`` and ``with_format("webp")`` (each gives a new ``Asset``), and ``str(asset)``
is its URL. It is sent back as the bare hash. ``created_at`` on a ``User`` or ``Guild`` is
read from its id. ``member.display_name`` is the server
nickname, else the user's display name.

To get the file itself, ``download(url)`` returns its bytes as a :class:`Result` (a missing file is an
``Err`` with the HTTP ``status``): ``data = (await download(user.display_avatar.url)).unwrap()``,
or ``await download(message.attachments[0].url)``.

Objects act
-----------

An object that reaches a handler, or that you read from ``ctx.state``, is **bound to the
context**: it carries every action that makes sense for it, with the same arguments as the
matching :doc:`api` call.

.. code-block:: python

   await message.reply("pong")
   await message.react("👍")
   await member.timeout(until, reason="spam")
   await member.add_role(role_id)
   await member.send("You were warned.")
   await guild.ban(user_id, reason="raid")
   await channel.send(Draft("hi", embeds=[...]))
   await channel.bulk_delete(message_ids)

The actions are generated from the API, so there is one for each (``Guild`` has 62, ``Channel``
34, ``Message`` 16, ``Member`` 10 and ``User`` ``send`` and ``dm``), and a new operation shows up
on its object when the API is regenerated. Two naming rules:

* ``get`` becomes ``fetch``: ``await member.fetch()`` asks Discord for a fresh copy.
* A name the object already has gets ``fetch_`` in front. ``guild.roles`` is the roles the
  object carries; ``await guild.fetch_roles()`` asks Discord for them.

Objects also **navigate** through what the Gateway holds (:doc:`state`), with ``get_*``:
``await member.get_guild()``, ``get_roles()`` and ``get_permissions(channel_id)``;
``await message.get_channel()`` and ``get_guild()``; ``await channel.get_guild()``, ``get_parent()``
and ``permissions_for(user_id)``; ``await guild.get_members()``, ``get_member(id)``,
``get_channels()`` and ``get_roles()``. They never call Discord and return ``None`` when the
Gateway does not hold the answer.

An object you build by hand (``Message(id=..., channel_id=...)``) has no context, and its actions
raise a clear error; ``obj.bind(ctx)`` ties it to one.

Permissions
-----------

Discord sends permissions as a decimal string. On the views they are
:class:`Permissions`, a set of named flags: ``role.permissions``, an overwrite's ``allow``
and ``deny``, and ``member.permissions`` (on interactions: what the member may do in that
channel).

.. code-block:: python

   from micro.discord.permissions import Permissions

   if not interaction.member.permissions.allows(Permissions.MANAGE_MESSAGES):
     await interaction.respond(Draft("You need Manage Messages.", ephemeral=True))

   needed = Permissions.KICK_MEMBERS | Permissions.BAN_MEMBERS
   needed in role.permissions            # exactly these bits
   role.permissions.names                # ["kick_members", "ban_members", ...]

   @commands.slash("purge", default_member_permissions=Permissions.MANAGE_MESSAGES)
   async def purge(ctx: Context, interaction): ...

``allows`` is true for an administrator whatever else is set; ``in`` tests the bits
themselves. A ``Permissions`` is an ``int``, so it goes anywhere a number is wanted, and
it is written back to Discord as the string it expects. ``DiscordState.permissions``
(:doc:`state`) computes a member's effective permissions in a channel.

Text helpers
------------

``micro.discord.text`` has the small things message text needs:

.. code-block:: python

   from micro.discord import text

   text.escape(member.display_name)        # Markdown switched off: shown as typed
   text.escape_mentions(untrusted)         # @everyone and <@id> made inert
   text.timestamp(when, "R")               # "<t:1700000000:R>": "in 3 hours", per reader
   text.user(id), text.role(id), text.channel(id), text.command("ticket open", id)
   text.snowflake_time(message.id)         # when any Discord id was created
   text.time_snowflake(when)               # an id for before= / after= paging

Reference
---------

.. api::
   micro.discord.objects.Object
   micro.discord.objects.User
   micro.discord.objects.Member
   micro.discord.objects.Role
   micro.discord.objects.PermissionOverwrite
   micro.discord.objects.Channel
   micro.discord.objects.Guild
   micro.discord.objects.Attachment
   micro.discord.objects.Message
   micro.discord.asset.Asset
   micro.discord.files.download
   micro.discord.files.DownloadError
   micro.discord.enums.ChannelType
   micro.discord.enums.OverwriteType
   micro.discord.enums.InteractionType
   micro.discord.enums.CommandType
   micro.discord.enums.ButtonStyle
   micro.discord.enums.TextInputStyle
   micro.discord.permissions.Permissions
   micro.discord.text.escape
   micro.discord.text.escape_mentions
   micro.discord.text.timestamp
   micro.discord.text.TimestampStyle
   micro.discord.text.user
   micro.discord.text.role
   micro.discord.text.channel
   micro.discord.text.command
   micro.discord.text.snowflake_time
   micro.discord.text.time_snowflake
   micro.discord.text.DISCORD_EPOCH_MS
