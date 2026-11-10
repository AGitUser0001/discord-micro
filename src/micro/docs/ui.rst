Messages and components
=======================

``micro.discord.ui`` builds everything you send: embeds, mention rules, and **every
component Discord has** (classic buttons and selects, the layout components of "components
v2", and modal inputs). Builders are plain, frozen objects with a ``to_dict()``; every
place that takes a message (``ctx.respond``, ``api.create_message``, ``channel.send``)
accepts them, and anything a builder lacks can be passed as a plain dict instead.

.. code-block:: python

   from micro.discord.ui import (
     AllowedMentions, Button, Colour, Draft, Embed, EmbedField, StringSelect,
   )

   await channel.send(Draft(
     "Report ready",
     embeds=[Embed("Title", "Body", colour=Colour.BLURPLE, fields=[EmbedField("a", "b", inline=True)])],
     components=[Button("Open", custom_id="report.open"), Button("Docs", url="https://...")],
     allowed_mentions=AllowedMentions.only(users=[1]),
   ))

**Mentions never ping unless allowed.** If you pass no ``allowed_mentions`` Micro sends
``{"parse": []}``; ``AllowedMentions.only(users=..., roles=...)`` opts specific ones in.

Embeds
------

:class:`Embed` is a builder like the components: ``title``, ``description``, ``url``,
``colour``, ``timestamp`` (a ``datetime``), ``fields`` (:class:`EmbedField`),
``footer`` (:class:`EmbedFooter`), ``author`` (:class:`EmbedAuthor`), ``image`` and
``thumbnail``. A picture is a URL or an :class:`Upload`.

.. code-block:: python

   Embed(
     "Sales", "This week", colour=Colour.GREEN, image=chart,
     fields=[EmbedField("North", "12"), EmbedField("South", "9", inline=True)],
     footer=EmbedFooter("updated", icon=avatar_url),
     author=EmbedAuthor("Ada"),
   )

Embeds are immutable; ``dataclasses.replace`` gives a changed copy. Like components they
carry their limits (``embed.measures``, ``embed.length``): 256 title, 4096 description, 25
fields, 6000 characters between all of a message's embeds, ten embeds a message. They are
checked when the embed is serialized, with the same middleware (`hooks`) as the
components, and before anything is sent.

Messages are data
-----------------

An outgoing message is a :class:`Draft`: the text, embeds, components, files, mention rules
and flags that make it, held as a value. Nothing is sent until you hand it to something.

.. code-block:: python

   from micro.discord.ui import Button, Draft, Embed

   report = Draft(
     "Report ready",
     embeds=[Embed("Sales", image=chart)],
     components=[Button("Open", custom_id="report.open")],
     ephemeral=True,
   )

   await ctx.respond(report)                       # an interaction
   await ctx.edit_response(replace(report, content="Updated"))   # dataclasses.replace
   await channel.send(report)                      # a channel, a message edit, the API:
   await api.create_message(channel_id, report)    # every message method takes a Draft

A ``Draft`` is the **one way** to say what a message is: there are no separate ``embeds=``,
``components=``, ``files=`` or ``ephemeral=`` arguments to send it with, and a plain string
stands for a text-only ``Draft``. It is immutable and compares by value, so build it in a
helper, keep it in a table, return it from a function, assert on it in a test.
``dataclasses.replace(draft, content="...")`` gives a changed copy; ``draft.to_dict()`` is
the JSON Discord receives and ``draft.uploads`` the files that travel with it. It also takes
``reply_to`` (reply to a message), ``silent`` (no notification), ``suppress_embeds``, ``tts``
and, for edits, ``keep``.

**Editing.** A part left as ``None`` stays as it is on the message and an empty one clears
it: ``Draft(embeds=())`` removes the embeds, ``Draft(content="")`` the text,
``Draft(components=())`` the components. Files you add are added to the message;
``Draft(keep=[...])`` lists the existing attachments that stay (``keep=[]`` removes them all).

A ``Draft`` runs the serialize hooks like everything else, so one rule can touch every
outgoing message:

.. code-block:: python

   @hooks.serialize(only=Draft)
   def watermark(draft, next):
     data = next()
     data["content"] = (data.get("content") or "") + " [bot]"
     return data

The root classes
----------------

Everything in the UI is one of four kinds, each with a root you can ``isinstance`` against:
:class:`Component` (every message and modal component, version 1 and 2), :class:`Embed`,
:class:`Draft` (a whole message), and (in :doc:`objects`) :class:`Object`, the root of
everything Discord gives an id.

Colours
-------

Embeds take ``colour=`` and containers ``accent_colour=``. Give either a :class:`Colour`, or
anything it understands: a number, ``"#5865f2"`` (or the short ``"#58f"``), a name such as
``"blurple"``, or ``(r, g, b)``. A :class:`Colour` is an ``int``, so it works anywhere Discord
wants a colour.

.. code-block:: python

   Embed("Done", colour=Colour.GREEN)
   Embed("Done", colour="#57f287")
   Container(TextDisplay("hi"), accent_colour=(88, 101, 242))

   c = Colour.from_hex("#5865f2")      # also from_rgb(88, 101, 242), from_hsv(235, 0.64, 0.95)
   c.hex, c.rgb, c.hsv, c.r            # '#5865f2', (88, 101, 242), (...), 88
   c.lighten(0.2), c.darken(0.2)       # new colours, mixed toward white / black
   c.mix("red", 0.5)                   # half way to another colour (anything ``parse`` takes)

The named colours are ``BLURPLE``, ``GREEN``, ``YELLOW``, ``FUCHSIA``, ``RED``, ``WHITE``,
``DARK``, ``BLUE``, ``TEAL``, ``PURPLE``, ``ORANGE``, ``GOLD``, ``GREY`` and ``MAPLE``. Anything
outside 0 to 0xFFFFFF, an unknown name or a malformed hex string raises ``ValueError``.

Discord's JSON spells these ``color`` and ``accent_color``; Micro's API spells them ``colour``
and sends the wire names for you. The object views do the same with pydantic aliases:
``role.colour`` and ``user.accent_colour`` are :class:`Colour` values that read and write
``color`` / ``accent_color`` on the wire.

Classic components
------------------

Up to five buttons, or one select, per **row**. Pass them loose and :func:`rows` lays them
out (buttons fill rows of five, each select gets its own row); wrap them in
:class:`ActionRow` for control.

.. code-block:: python

   Button("Go", custom_id="go", style="success", emoji=Emoji("🚀"))   # also url=, or sku_id= (premium)
   StringSelect("pick", [SelectOption("a"), SelectOption("B", "b", "second", emoji=Emoji("🅱"))], max_values=2)
   UserSelect("who", defaults=[123]); RoleSelect("role")
   MentionableSelect("m", defaults=[Default.user(1), Default.role(2)])
   ChannelSelect("where", channel_types=["text", "voice", "category"])

A string select takes :class:`SelectOption` objects (its ``value`` is its label unless you
give one), a button or option an :class:`Emoji`, a section :class:`TextDisplay` objects and a
gallery :class:`MediaItem` objects: **no bare strings stand in for them**, so there is one
way to say each thing (``Emoji.parse("<:name:id>")`` reads an emoji from its text).

Button styles are ``primary``, ``secondary``, ``success``, ``danger`` (these take a
``custom_id``) and ``link`` / ``premium`` (a ``url`` / a ``sku_id`` instead). The select
builders cover string, user, role, mentionable and channel menus; ``Select`` is an alias of
``StringSelect``.

Layout components ("v2")
------------------------

A message that uses any of these sets Discord's ``IS_COMPONENTS_V2`` flag for you, and then
**cannot also have ``content`` or ``embeds``** (Micro raises before sending).

.. code-block:: python

   Container(
     TextDisplay("## Report"),
     Section(TextDisplay("**Ada** opened this"), TextDisplay("2 days ago"), accessory=Thumbnail("https://.../a.png")),
     Separator(),
     MediaGallery(MediaItem("https://.../1.png"), MediaItem("attachment://2.png", "alt text")),
     File("attachment://report.pdf"),
     ActionRow(Button("Close", custom_id="close")),
     accent_colour=Colour.BLURPLE,
   )

Modals
------

A :class:`Modal` has a ``custom_id``, a title and components: :class:`Label` wraps one input
(text, select, file upload, radio group, checkbox group or checkbox) and
:class:`TextDisplay` adds explanation.

.. code-block:: python

   Modal("form", "Report", [
     TextDisplay("Tell us what happened."),
     Label("Summary", TextInput("summary", max_length=100)),
     Label("Details", TextInput("details", style="paragraph", required=False)),
     Label("Kind", StringSelect("kind", [SelectOption("bug"), SelectOption("abuse")])),
     Label("Who", UserSelect("who")),
     Label("Evidence", FileUpload("files", max_values=3)),
     Label("Severity", RadioGroup("severity", [GroupOption("low"), GroupOption("high")])),
     Label("Notify", CheckboxGroup("notify", [GroupOption("me"), GroupOption("staff")])),
     Label("Confirm", Checkbox("sure")),
   ])

Open it with ``ctx.modal(...)`` and read the submission as described in :doc:`responding`.

Checking a message
------------------

**Every component counts, and every count has a limit.** Components keep their own counts and
**accumulate** the ones inside them as they are built, the way discord.py does:

.. code-block:: python

   box = Container(TextDisplay("hi"), ActionRow(Button("Go", custom_id="go")))
   box.components_count     # 4: the container, the text, the row, the button
   box.text_count           # 2: characters of Text Display content inside it
   box.measures             # every count with its limit, from Discord's own models

* **Text is measured the way Discord measures it: in UTF-16 code units** (:func:`utf16_length`), so a
  character outside the basic plane such as 😀 counts as 2. Every text count and limit here uses it;
  Python's ``len`` would undercount.
* ``components_count`` (this component and everything inside it) and ``text_count`` (characters
  of Text Display content inside it) are attributes set when it is constructed, summed from its
  children. Nothing re-walks JSON.
* ``measures`` lists each count with its limit as :class:`Measure` objects (``name``, ``count``,
  ``limit``, ``minimum``, ``ok``): a row's children (5), a section's texts (3), a gallery's items
  (10), a Text Display's content (4000), a button's label (80), a label's text (45) and
  description (100), a text input's value (4000) and placeholder (100), custom IDs (100),
  select options (25), and so on. The limits are read from Discord's generated request models,
  so they cannot drift from what Discord enforces.
* A message has two limits of its own, totals over everything nested: **40 components**
  (:data:`MAX_COMPONENTS`) and **4000 characters of Text Display content** (:data:`MAX_TEXT`).
  :func:`message_measures` gives them for a list of components.

**Reading capacities (for chunking).** Every component, and every component *class*, also has
three plain numbers that say how much fits, so code that splits content into rows and messages
can read them instead of hard-coding Discord's limits:

* ``count``: how much of its main dimension it holds;
* ``max``: that dimension's limit (``None`` when it has none), readable on the class too, as in
  ``ActionRow.max``; ``remaining`` is ``max - count``;
* ``slots``: what it costs inside its parent's ``count``. It is 1, except that **a select takes
  a whole action row (5)**, so a row's ``count`` is the sum of its items' ``slots``, not how
  many items it has, and a select plus a button is 6 of 5.

.. list-table::
   :header-rows: 1
   :widths: 24 38 14 24

   * - Component
     - ``count`` is
     - ``max``
     - ``slots``
   * - ``ActionRow``
     - slots used by its items
     - 5
     - 1
   * - ``Button``
     - characters of its label
     - 80
     - 1
   * - ``StringSelect``
     - options
     - 25
     - **5**
   * - ``UserSelect``, ``RoleSelect``, ``MentionableSelect``, ``ChannelSelect``
     - default values
     - 25
     - **5**
   * - ``Section``
     - texts
     - 3
     - 1
   * - ``TextDisplay``
     - characters of content
     - 4000
     - 1
   * - ``Thumbnail``
     - characters of description
     - 1024
     - 1
   * - ``MediaGallery``
     - items
     - 10
     - 1
   * - ``Container``
     - components in it, in all (itself included)
     - 40
     - 1
   * - ``TextInput``
     - characters of its value
     - 4000
     - 1
   * - ``Label``
     - characters of its label
     - 45
     - 1
   * - ``RadioGroup``, ``CheckboxGroup``
     - options
     - 10
     - 1
   * - ``Modal``
     - components
     - 5
     - 1
   * - ``File``, ``Separator``, ``Checkbox``, ``FileUpload``
     - 0
     - none
     - 1

What an item costs in a *message* is its ``components_count`` (a row of four buttons is 5), against
:data:`MAX_COMPONENTS` and, for text, ``text_count`` against :data:`MAX_TEXT`. A chunker can pack
a row without sending anything:

.. code-block:: python

   row = ActionRow()
   for item in items:                       # buttons and selects
     if item.slots > row.remaining:         # a select needs the whole row
       rows.append(row)
       row = ActionRow()
     row = ActionRow(*row.components, item)

**Checking is serialization middleware.** :func:`check_limits` is registered by default on
``hooks.serialize``: when a component is serialized it raises ``ValueError`` naming every count
that is out of bounds (``ActionRow: components is 6; Discord allows 5.``). Building a component
never fails, so you can assemble and then fix. The message-wide totals are checked when a message
is assembled (``ctx.respond``, ``channel.send``, the API methods) and by :func:`validate`.
``hooks.remove(check_limits)`` turns it off, for sending what Discord might one day accept.

:func:`validate` checks components against Discord's own generated request models, limits
included, and raises ``pydantic.ValidationError``. :func:`message_body` is what
``ctx.respond`` and the API use to assemble content, embeds, components and flags into a
body (it enforces the v2 rule above); :func:`is_v2` and :func:`rows` are its parts.

Intercepting construction and serialization
-------------------------------------------

A rule that applies to *every* component (sign every custom ID, prefix them, forbid a
style, stamp a tracking field) belongs in one place, not at every call site. ``hooks``
runs **middleware** around the two moments a component has: building it (``Button(...)``)
and serializing it (``component.to_dict()``, which a message or modal also calls on its
children).

.. code-block:: python

   from micro.discord.ui import Button, hooks

   @hooks.build(only=Button)                 # construction: change the arguments, or the result
   def default_style(call, next):
     call.kwargs.setdefault("style", "secondary")
     return next()

   @hooks.serialize                          # serialization: change the JSON
   def tag(component, next):
     data = next()
     if "custom_id" in data:
       data["custom_id"] = "v2." + data["custom_id"]
     return data

   Button("Go", custom_id="go").to_dict()    # secondary style, custom_id "v2.go"

* **Build middleware** gets a :class:`Construction` (``cls``, ``args``, ``kwargs``, all
  changeable) and ``next``; calling ``next()`` builds the component (running the rest of the
  chain) and you return it, or return a different component instead.
* **Serialize middleware** gets the component and ``next``; ``next()`` is its JSON, which you
  return, changed or replaced.
* They nest in the order registered, first added outermost, like all Micro middleware
  (:doc:`middleware`), but are **synchronous**, because builders are.
* A component that build middleware constructs *itself* is built without the build chain
  (so replacing a button cannot recurse into the middleware that replaced it).
* ``only=Button`` (or a tuple of classes, subclasses included) limits one to those components.
* Nested components are covered: a ``Container`` of an ``ActionRow`` of ``Button``\ s runs
  the serialize middleware for each. **Plain dict components bypass both**, as they are
  already JSON.
* ``hooks.remove(fn)`` unregisters either kind; ``with hooks.scoped():`` restores the
  registered middleware on exit, for tests.
* The hooks are process-wide, so register them once at startup (an import in every
  process that sends components). With none registered, building and serializing cost
  nothing extra.

The motivating use is signing custom IDs without touching each call site, shown in full in
:doc:`middleware`.

Reference
---------

.. api::
   micro.discord.ui.AllowedMentions
   micro.discord.ui.Upload
   micro.discord.ui.Media
   micro.discord.ui.Draft
   micro.discord.ui.Component
   micro.discord.ui.Interactive
   micro.discord.ui.Embed
   micro.discord.ui.EmbedField
   micro.discord.ui.EmbedFooter
   micro.discord.ui.EmbedAuthor
   micro.discord.ui.embed_length
   micro.discord.ui.MAX_EMBEDS
   micro.discord.ui.MAX_EMBED_TEXT
   micro.discord.ui.uploads_in
   micro.discord.ui.attachments
   micro.discord.ui.Emoji
   micro.discord.ui.Button
   micro.discord.ui.SelectOption
   micro.discord.ui.Default
   micro.discord.ui.StringSelect
   micro.discord.ui.UserSelect
   micro.discord.ui.RoleSelect
   micro.discord.ui.MentionableSelect
   micro.discord.ui.ChannelSelect
   micro.discord.ui.ActionRow
   micro.discord.ui.TextDisplay
   micro.discord.ui.Thumbnail
   micro.discord.ui.Section
   micro.discord.ui.MediaItem
   micro.discord.ui.MediaGallery
   micro.discord.ui.File
   micro.discord.ui.Separator
   micro.discord.ui.Container
   micro.discord.ui.TextInput
   micro.discord.ui.GroupOption
   micro.discord.ui.RadioGroup
   micro.discord.ui.CheckboxGroup
   micro.discord.ui.Checkbox
   micro.discord.ui.FileUpload
   micro.discord.ui.Label
   micro.discord.ui.Modal
   micro.discord.ui.rows
   micro.discord.ui.is_v2
   micro.discord.ui.message_body
   micro.discord.ui.validate
   micro.discord.ui.Measure
   micro.discord.ui.message_measures
   micro.discord.ui.enforce
   micro.discord.ui.check_limits
   micro.discord.ui.MAX_COMPONENTS
   micro.discord.ui.MAX_TEXT
   micro.discord.ui.utf16_length
   micro.discord.ui.Hooks
   micro.discord.ui.Construction
   micro.discord.ui.BuildMiddleware
   micro.discord.ui.SerializeMiddleware

Colours live in ``micro.discord.colour``:

.. api::
   micro.discord.colour.Colour
   micro.discord.colour.ColourLike
