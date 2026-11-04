Projects
========

Micro is a library: your bot is its own project that depends on it.
``micro init`` creates the recommended layout; its templates ship with Micro,
so newer Micro versions create newer layouts.

.. code-block:: text

   mybot/
     pyproject.toml            depends on micro[all,accel]
     micro.toml                processes and their components
     src/mybot/
       services/               one module per service
         hello.py

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
   components = ["mybot.services.*"]

``mybot.services.*`` loads every component defined at module level in each
module of the package. Other targets: ``module:attribute`` (a component, a
list, or a class to instantiate).

Commands
--------

.. code-block:: console

   micro init NAME [--directory DIR]
   micro add service NAME

A service module:

.. code-block:: python

   from micro.discord.interactions import Commands, Interaction
   from micro.service import Service

   service = Service("tickets")
   commands = Commands(service)

   @commands.slash("tickets", description="tickets")
   async def tickets(ctx: Interaction) -> None:
     await ctx.reply("tickets is running.", ephemeral=True)

Share schemas between services from a plain module (``src/mybot/contracts.py``).
