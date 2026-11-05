Projects
========

Micro never manages your Python project; uv, pip, or anything else does.
``micro init`` only adds Micro's pieces, from templates that ship with Micro.

.. code-block:: console

   micro init                    # in the project directory
   micro add service NAME        # services/NAME/
   micro add example [NAME]      # list, or copy a bundled example

``micro init`` adds ``micro.toml``, a ``services`` package with a ``hello``
service, and ``.micro/`` and ``.env`` to ``.gitignore``. It follows your layout:

* ``src/<package>/`` exists: services go in ``src/<package>/services/``
  (target ``<package>.services.*``).
* otherwise: ``services/`` at the project root (target ``services.*``).

``micro add service`` writes the service folder wherever micro.toml's services
target points.

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

``package.*`` loads every component defined at module level in each service
folder (or module) of the package; adding a service never edits micro.toml. Other targets:
``module:attribute`` (a component, a list, or a class to instantiate).

A service is a folder; its ``__init__.py`` defines the components:

.. code-block:: python

   # services/tickets/__init__.py
   from micro.discord.interactions import Commands, Interaction
   from micro.service import Service

   service = Service("tickets")
   commands = Commands(service)

   @commands.slash("tickets", description="tickets")
   async def tickets(ctx: Interaction) -> None:
     await ctx.respond("tickets is running.", ephemeral=True)

Keep ``services/`` for services only, with the pieces of one service inside its
folder (``tickets/schemas.py``, ``tickets/views.py``, ...). Code more than one
service uses goes outside it, in a package of your own such as ``shared/``, so
the ``services.*`` target never has to guess what is a service.

Examples ship with Micro (``greeter``, ``audit``, ``chat``, ``notes``,
``ticker``); each is a self-contained service folder, and ``micro add example``
copies one into ``services/``. They share nothing: ``audit`` declares the
messages it listens for itself, because services agree through validated
messages, not shared code.
