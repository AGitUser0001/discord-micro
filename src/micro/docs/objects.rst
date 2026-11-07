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

Reference
---------

.. api::
   micro.discord.objects.User
   micro.discord.objects.Member
   micro.discord.objects.Role
   micro.discord.objects.PermissionOverwrite
   micro.discord.objects.Channel
   micro.discord.objects.Guild
   micro.discord.objects.Attachment
   micro.discord.objects.Message
