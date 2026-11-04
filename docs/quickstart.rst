Quickstart
==========

Install
-------

.. code-block:: console

   pip install "Micro[gateway,http,accel]"

Extras: ``gateway`` (Hikari), ``store`` (GraphQL store), ``http`` (bridge),
``accel`` (uvloop/winloop). ``micro up`` starts a local ``nats-server`` if none
is reachable; install the binary (the gAIt installer puts it in ``.venv/bin``).

A bot
-----

.. code-block:: python

   # app.py
   from micro.discord.interactions import Commands, Interaction
   from micro.service import Service

   bot = Service("hello")
   commands = Commands(bot)

   @commands.slash("hello", description="Say hello")
   async def hello(ctx: Interaction, name: str = "world") -> None:
     await ctx.reply(f"Hello, {name}!")

.. code-block:: toml

   # micro.toml
   name = "hello"

   [processes.all]
   components = [
     "micro.gateway:GatewayWorker",
     "micro.discord:DiscordHTTPWorker",
     "micro.discord.interactions:InteractionRouter",
     "micro.discord.interactions:CommandSync",
     "app:bot",
   ]

.. code-block:: console

   DISCORD_TOKEN=... micro up

``/hello`` is registered automatically. See ``examples/application`` for a
fuller bot (autocomplete, buttons, a modal, work queues, a background task).
