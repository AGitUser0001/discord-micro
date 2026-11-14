Responding
==========

Every interaction handler takes the same first two arguments: a :class:`Context` (how to reach
Discord) and an :class:`Interaction` (what the user did and every way to answer it), then the
command's own options:

.. code-block:: python

   @commands.slash("whois")
   async def whois(ctx: Context, interaction: Interaction, who: User) -> None:
     member = await ctx.state.member(interaction.guild_id, who.id)    # what the Gateway knows
     await interaction.respond(member.display_name if member else who.display_name)

A context carries everything a handler reaches for, apart from the runtime:

* ``ctx.api``: every Discord operation (:doc:`api`).
* ``ctx.state``: what the Gateway connections hold (:doc:`state`), including the bot's own
  user (``await ctx.state.me()``) and every guild it is in (``await ctx.state.guilds()``).
* ``ctx.gateway``: the connections themselves: presence (``update_presence``), voice
  (``update_voice_state``), member lists (``request_guild_members``), ``status()``, intents.
* ``ctx.timers``: schedule something for later, cancel it, list what is pending.
* ``ctx.client``: request, emit or enqueue to your own services (:doc:`services`).
* ``ctx.store``: your durable records, in the Store (:doc:`data`).
* ``ctx.application_id``: your application's id.
* ``ctx.command_id(name)`` and ``ctx.mention_command(name)``: the id Discord gave one of your
  commands, and the clickable ``</name:id>`` (:doc:`commands`).

The interaction reaches the same context as ``interaction.context``. This page is about the
interaction.

``respond`` is the everyday call; it chooses the right Discord request from what the
interaction has already sent.

.. code-block:: python

   await interaction.respond(Draft("hi", ephemeral=True, embeds=[...], components=[...]))
   await interaction.defer()                       # button: silent, update mode. Command: "thinking..."
   await interaction.defer(thinking=True)          # button: "thinking..." (message mode)
   await interaction.edit_response("changed")
   await interaction.delete_response()
   await interaction.update_message("new content") # edit the message a button sits on
   await interaction.modal(modal)
   await interaction.autocomplete(["a", "b"])

What a call does depends on what came before:

.. list-table::
   :header-rows: 1
   :widths: 24 16 20 22 18

   * - after →
     - nothing
     - ``defer()``
     - ``defer(thinking=True)``
     - responded
   * - ``respond``
     - new message
     - follow-up
     - fills "thinking"
     - follow-up
   * - ``update_message``
     - edits
     - edits original
     - **error**
     - **error**

A sequence Discord would reject raises :class:`InvalidResponse` or :class:`AlreadyResponded`
naming the state, **before anything is sent**. ``update_message`` needs the source message
of a component (or of a modal opened from one).

**Nothing defers automatically.** An interaction you do not answer within three seconds fails
for the user with "The application did not respond". ``defer()`` first when the work is slow
(or use ``defers()`` middleware, :doc:`middleware`). After 15 minutes the token expires and
calls raise :class:`InteractionExpired`.

A message as a value
--------------------

A message is a :class:`Draft` (:doc:`ui`): ``interaction.respond``, ``edit_response`` and
``update_message`` each take one, or a plain string for text only. There is no other way to
pass embeds, components, files or ``ephemeral``, so a message is always one value you can
build away from the handler, test, and reuse.

.. code-block:: python

   await interaction.respond("hi")
   await interaction.respond(Draft("hi", ephemeral=True, embeds=[Embed("T")]))

Files
-----

A file is an :class:`Upload`: a name and its bytes. Put it **where it is shown** and the
message attaches it; there is no second list to keep in step and no ``attachment://`` URL
to spell.

.. code-block:: python

   from micro.discord.ui import (
     Draft, Embed, File, MediaGallery, MediaItem, Section, TextDisplay, Thumbnail, Upload,
   )

   chart = Upload("chart.png", png_bytes, description="Sales by week")

   await interaction.respond(Draft(components=[MediaGallery(MediaItem(chart))]))  # a picture
   await interaction.respond(Draft(components=[Section(TextDisplay("Sales"), accessory=Thumbnail(chart))]))
   await interaction.respond(Draft(components=[File(Upload.text("log.txt", log))]))   # a download
   await interaction.respond(Draft(embeds=[Embed("Sales", image=chart)]))         # in an embed

A file that is only attached, not shown, goes in the draft's ``files``:

.. code-block:: python

   await interaction.respond(Draft("Here you go.", files=[Upload.from_path("report.pdf")]))

``Upload.text(name, string)``, ``Upload.json(name, value)`` and ``Upload.from_path(path)``
build one from what you have. ``description=`` is its alt text, ``spoiler=True`` hides it
behind a click. The same ``Upload`` used in several places is sent once; two different
files under one name are refused, before anything is sent.

Files work on the first response, the answer to a deferral, follow-ups and edits. On an
edit new files are **added** and the ones already there stay; ``keep`` says otherwise:

.. code-block:: python

   await interaction.update_message(Draft(components=[MediaGallery(MediaItem(new_chart))], keep=[]))    # replace all
   await interaction.edit_response(Draft("trimmed", keep=[interaction.message.attachments[0]]))      # keep one

(Alt text on a file added by an edit is sent only together with ``keep``, because naming
the files is what tells Discord which ones the message has.)

An interaction received over HTTP (:doc:`endpoint`) is answered in a JSON reply that
cannot carry files, so there ``respond`` acknowledges in that reply and sends the message
with its files straight after; nothing changes in your code. Every message method of the API
(``channel.send``, ``create_message``, ...) attaches shown uploads the same way.

Anything ``respond`` does not cover
-----------------------------------

For a response type ``respond`` has no method for, call the API directly:
``ctx.api.create_interaction_response(interaction.id, interaction.token, type=..., data=...)``. It sends
exactly that and never decides or refuses, so it does not update ``interaction.responded`` or
``interaction.state``; you are in charge of the sequence.

Reading the interaction
-----------------------

.. list-table::
   :header-rows: 1
   :widths: 32 68

   * - Attribute
     - Meaning
   * - ``interaction.user``, ``interaction.member``
     - Who acted; ``member`` is ``None`` in DMs.
   * - ``interaction.guild_id``, ``interaction.channel_id``, ``interaction.locale``
     - Where, and the user's language.
   * - ``interaction.message``
     - The message a component sits on.
   * - ``interaction.command_name``, ``interaction.custom_id``
     - The command invoked, or the id of the component or modal.
   * - ``interaction.submitted``
     - What the user sent (below): options, a select's values, a modal's fields, and the
       users, roles, channels and files they refer to.
   * - ``interaction.route``
     - What the matched route extracted from the custom id (:doc:`components`).
   * - ``interaction.state``
     - What has been sent so far, an :class:`InteractionState` (``NEW``, then ``MESSAGE``,
       ``DEFERRED_MESSAGE``, ``UPDATED``, ``MODAL``, ...). ``interaction.responded`` and ``interaction.deferred``
       are the two questions you usually ask of it.
   * - ``interaction.age``, ``interaction.expired``
     - Seconds since Discord created it; whether the token has expired.
   * - ``interaction.responded``, ``interaction.deferred``
     - What has been sent.
   * - ``interaction.type``
     - The kind, an :class:`InteractionType`: ``interaction.type is InteractionType.MODAL_SUBMIT``.

What the user sent
~~~~~~~~~~~~~~~~~~

Everything the user sent is under ``interaction.submitted`` (a :class:`Submitted`), so typing
``interaction.submitted.`` lists just that:

* ``options``: a command's options by name, subcommands included. Raw values: ids stay
  strings (``resolved`` has the entities they name).
* ``values``: a select menu's chosen values.
* ``inputs``: everything a modal submission holds, by ``custom_id``: strings for text and
  radio inputs (``None`` for nothing chosen), lists for selects, checkbox groups and uploads,
  a bool for a checkbox. ``fields`` is just the text-like ones as strings.
* ``users("who")``, ``members("who")``, ``roles(...)``, ``channels(...)`` and
  ``attachments("files")`` return typed objects (:doc:`objects`) resolved from Discord's
  lookup table. A select on a message works the same without the name (``users()``).
* ``choices(custom_id)`` is what a select, checkbox group or upload picked, as raw values,
  and ``resolved`` holds the whole lookup table (:class:`Resolved`).

Doing anything else
~~~~~~~~~~~~~~~~~~~

``interaction.context.api`` is the whole Discord API (:doc:`api`), and ``interaction.channel_ref``,
``interaction.guild_ref``, ``interaction.member_ref``, ``interaction.user_ref`` and ``interaction.message_ref`` are this
interaction's own objects, ready for ``send``, ``timeout``, ``reply`` and so on.

Errors
------

.. api::
   micro.discord.interactions.InvalidResponse
   micro.discord.interactions.AlreadyResponded
   micro.discord.interactions.InteractionExpired

Text helpers
------------

``micro.discord.text`` is the small toolbox for message text, all plain functions:

.. code-block:: python

   from micro.discord import text

   text.escape(member.display_name)          # Markdown switched off, links kept: shown as typed
   text.escape_mentions(note)                # @everyone and <@id> made inert
   text.timestamp(when, "R")                 # <t:...:R>, "3 hours ago"
   text.user(user_id)                        # <@id>; also role, channel and command
   text.snowflake_time(message.id)           # when an id was created

Escape anything a user typed before putting it inside your own formatting.

Reference
---------

.. api::
   micro.discord.interactions.Context
   micro.discord.interactions.Interaction
   micro.discord.interactions.Submitted
   micro.discord.interactions.Resolved
