Projects
========

Micro never manages your Python project; uv, pip, or anything else does.
``micro init`` only adds Micro's pieces.

.. code-block:: console

   micro init                    # in the project directory
   micro services add NAME       # a new, empty service in services/NAME/
   micro services list           # the services here, and where each came from
   micro pkg add builtin/chat    # an example, fetched and copied to services/chat/
   micro pkg list                # every package source has

``micro init`` adds ``micro.toml``, a ``services`` package with a ``hello``
service (fetched, so it needs the network and git; offline it adds everything else
and tells you to run ``micro pkg add builtin/hello`` later), and ``.micro/`` and ``.env`` to
``.gitignore``. It follows your layout:

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
   async def tickets(interaction: Interaction) -> None:
     await interaction.respond(Draft("tickets is running.", ephemeral=True))

Keep ``services/`` for services only, with the pieces of one service inside its
folder (``tickets/schemas.py``, ``tickets/views.py``, ...). Code more than one
service uses goes outside it, in a package of your own such as ``shared/``, so
the ``services.*`` target never has to guess what is a service.

Packages
--------

Examples are *packages*: a folder you copy into ``services/`` and then own.
``hello`` (what ``init`` adds), and the examples ``greeter``, ``audit``, ``chat``,
``notes``, ``ticker``, ``health`` and ``custom`` (members make their own
commands at runtime; needs a store). They share nothing: ``audit`` declares the
messages it listens for itself, because services agree through validated
messages, not shared code. (``micro services add tickets`` is different: it writes a
blank service from a built-in template, with nothing to fetch or upgrade.)

A package comes from a *source*: a git repository (or a folder) whose ``packages/``
folder holds one folder per package. Nothing is bundled with Micro. The default
source, ``builtin``, is Micro's own repository; the packages need ``git`` and the
network to ``add``, ``status`` and ``upgrade``.

.. code-block:: console

   micro pkg list                                       # every source, and what you added from it
   micro pkg add builtin/chat                           # always SOURCE/NAME
   micro pkg add builtin/tpl tickets                    # a template takes a name
   micro pkg add builtin/chat --ref v0.3                # a tag, branch or commit

   micro pkg source add team git@github.com:acme/bot-packages.git /packages
   micro pkg add team/billing                           # from the source you added
   micro pkg source list
   micro pkg source remove team                         # added packages keep working

A source is a git URL or a folder on this machine (``micro pkg source add loc
./team-packages``). Give an https URL or an ssh one: Micro tries the other form of the
same address if the first fails, so a machine with only an ssh key, or only a
token, both work. ``micro pkg source add`` writes ``[sources.NAME]`` into
``micro.toml``, which you can edit by hand:

.. code-block:: toml

   [sources.team]
   url = "git@github.com:acme/bot-packages.git"
   path = "packages"          # the folder of packages inside the repository
   ref = "v2"                 # optional: a branch, tag or commit to follow

Without a ``ref`` a package follows the tag ``v<your Micro version>`` if the
repository has it, and its default branch otherwise. ``MICRO_PACKAGES_URL``
replaces the default source's address (a mirror, or a fork).

``micro.lock`` (commit it) records, per package, where it came from: the source, the
branch or tag it follows, the exact commit, and each file's hash as it was given to
you. That is how an upgrade can tell your edits from the source's changes:

.. code-block:: console

   micro pkg status             # each package against what its source has now
   micro pkg diff chat          # your files against upstream's
   micro pkg upgrade            # apply it, merging your edits
   micro pkg upgrade chat --ref main    # move one package to another branch, tag or commit
   micro pkg upgrade --theirs   # on a conflict, take upstream's file
   micro pkg upgrade --mine     # on a conflict, keep yours and mark upstream's as reviewed
   micro pkg forget chat        # stop tracking; the files stay

``upgrade`` fetches what each package's ref points at now and compares, per file,
the hash you were given, the file now, and the new version:

==========================================  ============================================
you, and upstream                           ``upgrade``
==========================================  ============================================
you did not edit it, upstream changed it    replaces the file
you edited it, upstream did not change it   keeps yours
upstream added a file                       adds it
upstream dropped a file you did not edit    removes it (an edited one is kept)
you deleted it, upstream did not change it  keeps it deleted
you and upstream both changed it            **merged** line by line (see below)
you deleted it, upstream changed it         **conflict**: left alone until you choose
==========================================  ============================================

A file you both changed is merged with git's three-way merge, against the commit you
installed (fetched again for the purpose; templates are rendered with your saved
name). Edits on different lines merge on their own. Edits to the same lines are
left as ``<<<<<<< yours`` / ``>>>>>>>`` markers for you to fix, and ``status`` keeps
flagging the file until they are gone. A lock without a commit (written by an
older Micro) has nothing to merge against, so both-changed files stay conflicts.

Markers and conflicts end ``upgrade`` with a non-zero exit status and name the
files. ``--theirs`` takes upstream's file for each; ``--mine`` keeps yours. After
``--mine`` the same upstream version is not raised again; the next change to
that file is.
