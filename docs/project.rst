Projects
========

Micro never manages your Python project; uv, pip, or anything else does.
``micro init`` only adds Micro's pieces, from templates that ship with Micro.

.. code-block:: console

   micro init                    # in the project directory
   micro add service NAME

``micro init`` adds ``micro.toml``, a services package with ``hello.py``, and
``.micro/`` to ``.gitignore``. It follows your layout:

* ``src/<package>/`` exists: services go in ``src/<package>/services/``
  (target ``<package>.services.*``).
* otherwise: ``services/`` at the project root (target ``services.*``).

``micro add service`` writes the module wherever micro.toml's services target
points.

micro.toml
----------

.. code-block:: toml

   name = "mybot"

   [processes.discord]                  # Discord plumbing
   components = [
     "micro.gateway:GatewayWorker",
     "micro.discord:DiscordHTTPWorker",
     "micro.discord.interactions:InteractionRouter",
     "micro.discord.interactions:CommandSync",
   ]

   [processes.app]                      # your code; roll it freely
   components = ["services.*"]

``package.*`` loads every component defined at module level in each module of
the package; adding a service never edits micro.toml. Other targets:
``module:attribute`` (a component, a list, or a class to instantiate).

A service module:

.. code-block:: python

   from micro.discord.interactions import Commands, Interaction
   from micro.service import Service

   service = Service("tickets")
   commands = Commands(service)

   @commands.slash("tickets", description="tickets")
   async def tickets(ctx: Interaction) -> None:
     await ctx.reply("tickets is running.", ephemeral=True)

Share schemas between services from a plain module next to ``services``.
