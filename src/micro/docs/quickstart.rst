Quickstart
==========

Micro is a library: add it to your project with whatever manages it.

.. code-block:: console

   uv add discord-micro    # or: pip install "discord-micro[all,accel]"
   micro init              # (uv run micro init) adds micro.toml and services/hello/
   echo 'DISCORD_TOKEN=...' > .env
   micro dev

Project commands read ``.env`` next to ``micro.toml``; variables already set in
the environment win, and ``micro init`` adds ``.env`` to ``.gitignore``.
``micro dev`` runs everything on this machine: it starts a local ``nats-server`` when
none is reachable (see :doc:`deploy` to run the server apart; install the
binary: ``brew install nats-server``, or the release archive on Linux).
``/hello`` appears in Discord once ``CommandSync`` registers it.
``micro invite`` prints the link that adds the bot to a server.

Next:

.. code-block:: console

   micro services add tickets    # a new service folder, loaded automatically
   micro dev roll app            # deploy your changes without dropping the Gateway

``micro pkg list`` shows the examples (requests and events, work queues, buttons
and a modal, the store, a background task, ``health`` for streams and consumers
via ``/health``). They are fetched from a git source, so ``micro pkg add`` needs
git and the network; ``micro pkg upgrade`` merges newer versions into your edited
copies. See :doc:`project`.

Two examples need a little setup: ``chat``'s ``!ping`` reads message text, so set
``DISCORD_INTENTS=unprivileged,message_content`` and enable the Message Content
intent in the developer portal (:doc:`discord`); ``notes`` needs a store process
in ``micro.toml`` (:doc:`store`).
