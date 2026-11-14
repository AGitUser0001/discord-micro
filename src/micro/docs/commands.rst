Commands
========

:class:`Commands` declares slash commands, user commands and message commands from typed
Python functions. The function's parameters become the command's options; Micro builds
Discord's definition, converts the submitted values back into Python objects, and hands you
an :class:`Interaction` (``interaction``) first.

.. code-block:: python

   from typing import Annotated, Literal
   from micro.discord.interactions import Commands, Interaction, Option
   from micro.discord.objects import Member, Message, User

   commands = Commands(service, guild_ids=[...])   # guild_ids optional: guild commands

   @commands.slash("ticket", description="Open a ticket")
   async def ticket(
     ctx: Context,
     interaction: Interaction,
     topic: Annotated[str, Option("What about", max_length=100)],
     level: Literal["low", "high"] = "low",
     assignee: User | None = None,
   ) -> None:
     await interaction.respond(f"Opened {topic}")

   @ticket.autocomplete("topic")
   async def topics(ctx: Context, interaction: Interaction, value: str) -> list[str]:
     return [t for t in ("billing", "bug") if t.startswith(value)]

   admin = commands.group("admin", description="Admin tools")

   @admin.command("purge")
   async def purge(ctx: Context, interaction: Interaction, count: int) -> None: ...

   @commands.user("Report")
   async def report(ctx: Context, interaction: Interaction, member: Member) -> None: ...

   @commands.message("Quote")
   async def quote(ctx: Context, interaction: Interaction, message: Message) -> None: ...

Options
-------

An option's Discord type comes from the parameter's annotation:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Annotation
     - Discord option
   * - ``str``, ``int``, ``float``, ``bool``
     - string, integer, number, boolean
   * - ``User`` or ``Member``
     - user (you get a ``User`` / a ``Member`` with the resolved data)
   * - ``Role``, ``Channel``, ``Attachment``
     - role, channel, attachment
   * - ``Mentionable`` (or ``User | Role``)
     - user or role; you get whichever it was
   * - ``Literal["a", "b"]``
     - string/number with fixed **choices**
   * - ``X | None``, or a default
     - the option is **optional**

Required options must come before optional ones, as Discord demands (Micro raises when you
get the order wrong). ``Annotated[T, Option(...)]`` adds a description, a different name,
``choices`` (``Choice(name, value)`` for display names), ``min_value`` / ``max_value``,
``min_length`` / ``max_length``, ``channel_types`` and localizations.

Command settings
----------------

``slash(name, *, description, guild_ids, default_member_permissions, contexts,
integration_types, nsfw, name_localizations, description_localizations)``. Names must be
lowercase and 1 to 32 characters of letters, digits, ``-`` and ``_``. ``guild_ids`` defaults
to the ``Commands(...)`` value; empty means a global command. ``user`` and ``message`` take
the same settings (see :class:`MenuSettings`) and a name with spaces and capitals.

Groups
~~~~~~

``commands.group("admin")`` is a slash command whose subcommands are added with
``@group.command("name")``. A group can hold one more level (``group.group("x")``), which is
the most Discord allows. Their key for middleware scopes is the dotted path (``admin.purge``).

Autocomplete
~~~~~~~~~~~~

``@command.autocomplete("option")`` registers suggestions for a string, integer or number
option. The function gets the text typed so far and returns up to 25 choices (plain values
or :class:`Choice`). It runs with the same three-second limit; a slow lookup should answer
fast and let the user keep typing.

Behaviour worth knowing
-----------------------

* **Definitions are declared, not sent.** The :class:`CommandSync` component registers them
  once every live replica agrees (:doc:`command-sync`).
* **Old and new versions coexist.** An option the handler does not declare is ignored, and
  an optional option it does declare falls back to its default. A *required* option Discord
  did not send raises :class:`CommandOutdated`, and the user is told "This command was just
  updated. Please try again." while a rollout converges.
* **Handlers must be ``async``.**
* To make commands at runtime instead of in code, see :doc:`runtime-commands`.

Command ids and mentions
------------------------

Discord gives every command an id when it is synced, and Micro keeps them. Use them to
point at a command in a message, where Discord shows it as a clickable chip:

.. code-block:: python

   await interaction.respond(f"Open one with {await ctx.mention_command('ticket open')}")
   found = await ctx.command_id("ticket")                    # the id, or None before the first sync
   menu = await ctx.command_id("Say hi", type=CommandType.USER)   # a context-menu command

``mention_command`` takes the name with its subcommand (``"ticket open"``) and looks up the
top-level command's id: a guild's own command first, then the global one (pass ``guild_id=``).
Only slash commands can be mentioned; without a stored id it falls back to plain, escaped
text (``/ticket open``). For a context-menu command, ``command_id`` takes the exact name
and ``type`` (``CommandType.USER`` or ``CommandType.MESSAGE``).

Reference
---------

.. api::
   micro.discord.interactions.Commands
   micro.discord.interactions.Command
   micro.discord.interactions.CommandGroup
   micro.discord.interactions.Option
   micro.discord.interactions.Choice
   micro.discord.interactions.Mentionable
   micro.discord.interactions.CommandOutdated
   micro.discord.interactions._templates.MenuSettings
