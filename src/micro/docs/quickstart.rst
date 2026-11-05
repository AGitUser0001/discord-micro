Quickstart
==========

Micro is a library: add it to your project with whatever manages it.

.. code-block:: console

   uv add micro            # or: pip install "micro[all,accel]"
   micro init              # (uv run micro init) adds micro.toml and services/hello/
   echo 'DISCORD_TOKEN=...' > .env
   micro up

Project commands read ``.env`` next to ``micro.toml``; variables already set in
the environment win, and ``micro init`` adds ``.env`` to ``.gitignore``.
``micro up`` starts a local ``nats-server`` when none is reachable (install the
binary: ``brew install nats-server``, or the release archive on Linux).
``/hello`` appears in Discord once ``CommandSync`` registers it.

Next:

.. code-block:: console

   micro add service tickets     # a new service folder, loaded automatically
   micro roll app                # deploy your changes without dropping the Gateway

``micro add example`` lists bundled examples (requests and events, work queues,
buttons and a modal, the store, a background task); see :doc:`project`.
