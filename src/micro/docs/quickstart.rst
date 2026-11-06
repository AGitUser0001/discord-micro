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

``micro pkg list`` shows the bundled examples (requests and events, work queues,
buttons and a modal, the store, a background task); ``micro pkg upgrade`` brings
them up to date after a Micro upgrade. See :doc:`project`.
