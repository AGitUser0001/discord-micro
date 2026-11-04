Quickstart
==========

Micro is a library: add it to your project with whatever manages it.

.. code-block:: console

   uv add micro            # or: pip install "micro[all,accel]"
   micro init              # (uv run micro init) adds micro.toml and services/hello.py
   DISCORD_TOKEN=... micro up

``micro up`` starts a local ``nats-server`` when none is reachable (install the
binary: ``brew install nats-server``, or the release archive on Linux).
``/hello`` appears in Discord once ``CommandSync`` registers it.

Next:

.. code-block:: console

   micro add service tickets     # a new service module, loaded automatically
   micro roll app                # deploy your changes without dropping the Gateway

See :doc:`project` for the layout and ``examples/bot`` for a fuller project
(requests, events, work queues, buttons, a modal, a background task).
