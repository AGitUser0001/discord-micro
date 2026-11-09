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

* event payloads annotated with a view, and ``ctx.user``, ``ctx.member``, ``ctx.message``;
* command options (``user: User``, ``role: Role``, ``channel: Channel``, ``file: Attachment``);
* ``DiscordState`` reads (:doc:`cache`);
* resolved entities of a component or modal (``ctx.users()``, ``ctx.roles(...)``, see
  :doc:`responding`).

``User.display_name`` is the global name, or the username without one; ``mention`` on a
``User`` or ``Member`` is the ``<@id>`` form. ``Member.id`` is its user's id (``None`` if
Discord sent no user). The views are **frozen**: read them, do not assign to them.

``full()`` raises ``ValidationError`` when the payload was partial: a member resolved from
an interaction, for instance, has no ``user`` of its own.

``user.avatar_url()`` is the user's avatar (the default one Discord shows if they set
none), ``guild.icon_url()`` the server's icon or ``None``; both take ``size=``. ``created_at``
on a ``User`` or ``Guild`` is read from its id. ``member.display_name`` is the server
nickname, else the user's display name.

Permissions
-----------

Discord sends permissions as a decimal string. On the views they are
:class:`Permissions`, a set of named flags: ``role.permissions``, an overwrite's ``allow``
and ``deny``, and ``member.permissions`` (on interactions: what the member may do in that
channel).

.. code-block:: python

   from micro.discord.permissions import Permissions

   if not ctx.member.permissions.allows(Permissions.MANAGE_MESSAGES):
     await ctx.respond("You need Manage Messages.", ephemeral=True)

   needed = Permissions.KICK_MEMBERS | Permissions.BAN_MEMBERS
   needed in role.permissions            # exactly these bits
   role.permissions.names                # ["kick_members", "ban_members", ...]

   @commands.slash("purge", default_member_permissions=Permissions.MANAGE_MESSAGES)
   async def purge(ctx): ...

``allows`` is true for an administrator whatever else is set; ``in`` tests the bits
themselves. A ``Permissions`` is an ``int``, so it goes anywhere a number is wanted, and
it is written back to Discord as the string it expects. ``DiscordState.permissions``
(:doc:`cache`) computes a member's effective permissions in a channel.

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
