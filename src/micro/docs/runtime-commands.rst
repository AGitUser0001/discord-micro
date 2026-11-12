Runtime commands
================

:class:`Commands` are fixed when the code is written. :class:`RuntimeCommands` are for
commands that **people create while the bot runs**: a bot's custom commands, per-server
commands, commands that appear and disappear with a setting. You add and remove them from
running code, and one handler runs all of them.

.. code-block:: python

   from micro.discord.interactions import RuntimeCommands, option

   dynamic = RuntimeCommands(service)

   @dynamic.handler
   async def run(ctx: Context, interaction: Interaction) -> None:
     body = await lookup(interaction.guild_id, interaction.command_name)   # your own storage
     await interaction.respond(body)

   await dynamic.add("hello", "Say hello", guild_id=1234,
                     options=[option("who", "Who to greet")])
   await dynamic.remove("hello", guild_id=1234)

Adding and removing
-------------------

``add(name, description, *, guild_id, options, kind, default_member_permissions, nsfw)``
creates a command or changes its definition.

* Without ``guild_id`` the command is **global**. With one it is registered in that guild
  only. Adding the same name for another guild adds a *scope*: it is still one command, so
  use ``interaction.guild_id`` inside the handler to tell the guilds apart.
* ``options`` is a list of :func:`option` values (``option("who", "Who", kind="user",
  required=True, choices=[...])``). ``kind`` is 1 (slash, the default), 2 (user menu) or 3
  (message menu).
* ``remove(name, *, guild_id=None, kind=1)`` drops one scope, and the command itself goes
  when its last scope does. It returns whether the command existed.
* ``await dynamic.commands()`` lists what exists, keyed ``type:name`` with its ``guild_ids``.

The handler
-----------

``@dynamic.handler`` is one ``async def f(ctx: Context, interaction)`` for every runtime command. ``interaction.command_name``
is the invoked name and ``interaction.submitted.options`` the submitted options (``{"who": "bo"}``).
``@dynamic.autocomplete`` takes ``async def f(ctx: Context, interaction, value)`` and returns choices for options you
declared with ``autocomplete=True`` in a raw option dict.

How it works
------------

* Definitions are stored in the shared state table (``rtcmd.<type>.<name>``), so they **survive
  restarts** and are visible to every replica and every service with a ``RuntimeCommands``.
* :class:`CommandSync` watches that table and registers a change with Discord within moments.
  Unlike declared commands, runtime commands are applied **immediately**, not held back
  until every replica of a rollout agrees.
* Each command gets the same kind of durable consumer as a declared one, started on every
  service that uses ``RuntimeCommands`` as soon as the command exists and stopped when it is
  removed.
* A name that is **also declared in code** is skipped (the declared one wins) and a warning
  is logged. Pick names that do not clash.
* This manages the *commands*. What a custom command *says* belongs in your own storage; the
  ``custom`` package (``micro pkg add builtin/custom``) is a complete example built on the
  :doc:`store`.

Reference
---------

.. api::
   micro.discord.interactions.RuntimeCommands
   micro.discord.interactions.option
