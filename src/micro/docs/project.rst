Projects
========

Micro never manages your Python project; uv, pip, or anything else does.
``micro init`` only adds Micro's pieces.

.. code-block:: console

   micro init                    # in the project directory
   micro services add NAME       # a new, empty service in services/NAME/
   micro services list           # the services here, and where each came from
   micro pkg add chat            # a bundled example, copied to services/chat/
   micro pkg list                # everything Micro ships

``micro init`` adds ``micro.toml``, a ``services`` package with a ``hello``
service, and ``.micro/`` and ``.env`` to ``.gitignore``. It follows your layout:

* ``src/<package>/`` exists: services go in ``src/<package>/services/``
  (target ``<package>.services.*``).
* otherwise: ``services/`` at the project root (target ``services.*``).

``micro pkg add`` writes the service folder wherever micro.toml's services target
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

Packages
--------

Everything Micro ships for your services is a *package*: a folder you copy into
``services/`` and then own. ``hello`` (what ``init`` adds), the blank ``service``
template (``micro services add tickets`` is ``micro pkg add service tickets``), and the
examples ``greeter``, ``audit``, ``chat``, ``notes`` and ``ticker``. They share
nothing: ``audit`` declares the messages it listens for itself, because services
agree through validated messages, not shared code.

A package comes from a *source*, a folder of packages. The default is the builtin
source inside Micro. Name others in micro.toml, such as a team's shared services:

.. code-block:: toml

   [sources]
   team = "../team-packages"      # each folder inside it is a package

.. code-block:: console

   micro pkg list                              # every source, and what you added from it
   micro pkg add billing --source team
   micro pkg add billing --source ../team-packages   # or a folder directly

``micro.lock`` remembers each package's source, so ``status`` and ``upgrade`` compare
it with the right one.

Because the copy is yours to edit, ``micro.lock`` (commit it) records each file as
Micro gave it to you. That is how a newer Micro can offer updates without
overwriting your work:

.. code-block:: console

   micro pkg status             # each package against what this Micro ships
   micro pkg diff chat          # your files against Micro's
   micro pkg upgrade            # apply what is safe
   micro pkg upgrade --theirs   # on conflicts, take Micro's
   micro pkg upgrade --mine     # on conflicts, keep yours and mark Micro's as reviewed
   micro pkg forget chat        # stop tracking; the files stay

``upgrade`` compares three things per file: what Micro gave you, what is there now,
and what this Micro ships.

=========================================  ==========================================
you, and Micro                             ``upgrade``
=========================================  ==========================================
you did not edit it, Micro changed it      replaces the file
you edited it, Micro did not change it     keeps yours
Micro added a file                         adds it
Micro dropped a file you did not edit      removes it (an edited one is kept)
you deleted it, Micro did not change it    keeps it deleted
you and Micro both changed it              **conflict**: left alone until you choose
you deleted it, Micro changed it           **conflict**: left alone until you choose
=========================================  ==========================================

A conflict ends ``upgrade`` with a non-zero exit status and names the files;
nothing is overwritten until you say ``--theirs`` or ``--mine``. After ``--mine``
the same Micro version is not raised again; the next change to that file is.
