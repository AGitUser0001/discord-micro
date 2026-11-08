Messages and components
=======================

``micro.discord.ui`` builds everything you send: embeds, mention rules, and **every
component Discord has** (classic buttons and selects, the layout components of "components
v2", and modal inputs). Builders are plain, frozen objects with a ``to_dict()``; every
place that takes a message (``ctx.respond``, ``api.create_message``, ``channel.send``)
accepts them, and anything a builder lacks can be passed as a plain dict instead.

.. code-block:: python

   from micro.discord.ui import ActionRow, AllowedMentions, Button, StringSelect, embed

   await channel.send(
     "Report ready",
     embeds=[embed("Title", "Body", color=0x5865F2, fields=[("a", "b", True)])],
     components=[Button("Open", custom_id="report.open"), Button("Docs", url="https://...")],
     allowed_mentions=AllowedMentions.only(users=[1]),
   )

**Mentions never ping unless allowed.** If you pass no ``allowed_mentions`` Micro sends
``{"parse": []}``; ``AllowedMentions.only(users=..., roles=...)`` opts specific ones in.

Embeds
------

:func:`embed` builds the dictionary Discord wants: ``title``, ``description``, ``url``,
``color``, ``timestamp`` (a ``datetime`` or ISO string), ``fields`` (``(name, value,
inline)`` tuples), ``footer`` / ``footer_icon``, ``author`` / ``author_icon`` /
``author_url``, ``image``, ``thumbnail``. Discord's size limits are checked by
:func:`validate` below.

Classic components
------------------

Up to five buttons, or one select, per **row**. Pass them loose and :func:`rows` lays them
out (buttons fill rows of five, each select gets its own row); wrap them in
:class:`ActionRow` for control.

.. code-block:: python

   Button("Go", custom_id="go", style="success", emoji="🚀")   # also url=, or sku_id= (premium)
   StringSelect("pick", ["a", SelectOption("B", "b", "second", emoji="🅱")], max_values=2)
   UserSelect("who", defaults=[123]); RoleSelect("role")
   MentionableSelect("m", defaults=[Default.user(1), Default.role(2)])
   ChannelSelect("where", channel_types=["text", "voice", "category"])

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
     Section("**Ada** opened this", "2 days ago", accessory=Thumbnail("https://.../a.png")),
     Separator(),
     MediaGallery("https://.../1.png", MediaItem("attachment://2.png", "alt text")),
     File("attachment://report.pdf"),
     ActionRow(Button("Close", custom_id="close")),
     accent_color=0x5865F2,
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
     Label("Kind", StringSelect("kind", ["bug", "abuse"])),
     Label("Who", UserSelect("who")),
     Label("Evidence", FileUpload("files", max_values=3)),
     Label("Severity", RadioGroup("severity", ["low", "high"])),
     Label("Notify", CheckboxGroup("notify", ["me", "staff"])),
     Label("Confirm", Checkbox("sure")),
   ])

Open it with ``ctx.modal(...)`` and read the submission as described in :doc:`responding`.

Checking a message
------------------

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
   micro.discord.ui.embed
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
   micro.discord.ui.Hooks
   micro.discord.ui.Construction
   micro.discord.ui.BuildMiddleware
   micro.discord.ui.SerializeMiddleware
