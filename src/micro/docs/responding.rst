Responding
==========

Every handler receives an :class:`Interaction`, called ``ctx`` by convention. It carries
what Discord sent and every way to answer.

``respond`` is the everyday call; it chooses the right Discord request from what the
interaction has already sent.

.. code-block:: python

   await ctx.respond("hi", ephemeral=True, embeds=[...], components=[...])
   await ctx.defer()                       # button: silent, update mode. Command: "thinking..."
   await ctx.defer(thinking=True)          # button: "thinking..." (message mode)
   await ctx.edit_response("changed")
   await ctx.delete_response()
   await ctx.update_message("new content") # edit the message a button sits on
   await ctx.modal(modal)
   await ctx.autocomplete(["a", "b"])

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

Anything that takes ``content, embeds, components, ...`` also takes a :class:`Draft` in the
place of ``content``: ``await ctx.respond(Draft("hi", embeds=[...], ephemeral=True))``. It is the
same message held as data, so you can build it away from the handler, test it, and reuse
it (:doc:`ui`). Not both: a ``Draft`` plus loose pieces is a ``TypeError``.

Files
-----

A file is an :class:`Upload`: a name and its bytes. Put it **where it is shown** and the
message attaches it; there is no second list to keep in step and no ``attachment://`` URL
to spell.

.. code-block:: python

   from micro.discord.ui import Embed, File, MediaGallery, Section, Thumbnail, Upload

   chart = Upload("chart.png", png_bytes, description="Sales by week")

   await ctx.respond(components=[MediaGallery(chart)])                  # a picture
   await ctx.respond(components=[Section("Sales", accessory=Thumbnail(chart))])
   await ctx.respond(components=[File(Upload.text("log.txt", log))])    # a download
   await ctx.respond(embeds=[Embed("Sales", image=chart)])              # in an embed

A file that is only attached, not shown, goes in ``files=``:

.. code-block:: python

   await ctx.respond("Here you go.", files=[Upload.from_path("report.pdf")])

``Upload.text(name, string)``, ``Upload.json(name, value)`` and ``Upload.from_path(path)``
build one from what you have. ``description=`` is its alt text, ``spoiler=True`` hides it
behind a click. The same ``Upload`` used in several places is sent once; two different
files under one name are refused, before anything is sent.

Files work on the first response, the answer to a deferral, follow-ups and edits. On an
edit (``edit_response``, ``update_message``) new files are **added** and the ones already
there stay; ``keep=`` says otherwise:

.. code-block:: python

   await ctx.update_message(components=[MediaGallery(new_chart)], keep=[])   # replace all
   await ctx.edit_response("trimmed", keep=[ctx.message.attachments[0]])     # keep one

(Alt text on a file added by an edit is sent only together with ``keep=``, because naming
the files is what tells Discord which ones the message has.)

An interaction received over HTTP (:doc:`endpoint`) is answered in a JSON reply that
cannot carry files, so there ``respond`` acknowledges in that reply and sends the message
with its files straight after; nothing changes in your code. ``micro.discord.messages.send``
and every message method of the API (``channel.send``, ``create_message``, ...) attach
shown uploads the same way.

Low-level calls
---------------

The low-level layer is one Discord request each and never decides or refuses:
``create_initial_response(ResponseType.X, data)``, ``create_followup(body)``,
``edit_initial_response(body)``, ``delete_initial_response()``. They record what they sent
(so ``ctx.responded`` and ``ctx.state`` stay right) but trust you to know the sequence.
Use them for response types ``respond`` does not cover.

Reading the interaction
-----------------------

.. list-table::
   :header-rows: 1
   :widths: 32 68

   * - Attribute
     - Meaning
   * - ``ctx.user``, ``ctx.member``
     - Who acted; ``member`` is ``None`` in DMs.
   * - ``ctx.guild_id``, ``ctx.channel_id``, ``ctx.locale``
     - Where, and the user's language.
   * - ``ctx.message``
     - The message a component sits on.
   * - ``ctx.command_name``, ``ctx.option_values``
     - For commands: the name and the submitted options by name (subcommands included).
   * - ``ctx.custom_id``, ``ctx.values``
     - For components: the id, and a select's chosen values.
   * - ``ctx.inputs``, ``ctx.fields``
     - For modals: everything by custom id, and just the text-like fields.
   * - ``ctx.route``
     - What the matched route extracted from the custom id (:doc:`components`).
   * - ``ctx.state``
     - A dictionary middleware may use to pass things to the handler.
   * - ``ctx.age``, ``ctx.expired``
     - Seconds since Discord created it; whether the token has expired.
   * - ``ctx.responded``, ``ctx.deferred``
     - What has been sent.
   * - ``ctx.is_command``, ``is_component``, ``is_modal``, ``is_autocomplete``
     - The kind.

Modal and select input
~~~~~~~~~~~~~~~~~~~~~~

``ctx.inputs`` is everything a modal submission holds, by ``custom_id``: strings for text and
radio inputs (``None`` for nothing chosen), lists for selects, checkbox groups and
uploads, a bool for a checkbox. ``ctx.fields`` is just the text-like ones as strings. For the
entity fields, ``ctx.users("who")``, ``ctx.members("who")``, ``ctx.roles(...)``,
``ctx.channels(...)`` and ``ctx.attachments("files")`` return typed objects (:doc:`objects`)
resolved from Discord's lookup table. A select on a message works the same without the name
(``ctx.users()``). ``Interaction.resolved`` holds the whole table (:class:`Resolved`).

Doing anything else
~~~~~~~~~~~~~~~~~~~

``ctx.api`` is the whole Discord API (:doc:`api`), and ``ctx.channel_ref``,
``ctx.guild_ref``, ``ctx.member_ref``, ``ctx.user_ref`` and ``ctx.message_ref`` are this
interaction's own objects, ready for ``send``, ``timeout``, ``reply`` and so on.

Errors
------

.. api::
   micro.discord.interactions.InvalidResponse
   micro.discord.interactions.AlreadyResponded
   micro.discord.interactions.InteractionExpired

Reference
---------

.. api::
   micro.discord.interactions.Interaction
   micro.discord.interactions.Resolved
