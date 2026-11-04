Quickstart
==========

.. code-block:: console

   uvx --from micro micro init mybot     # or: pip install micro, then micro init mybot
   cd mybot
   DISCORD_TOKEN=... uv run micro up

``micro up`` starts a local ``nats-server`` when none is reachable (install the
binary: ``brew install nats-server``, or the release archive on Linux).
``/hello`` appears in Discord once ``CommandSync`` registers it.

Next:

.. code-block:: console

   uv run micro add service tickets       # src/mybot/services/tickets.py, loaded automatically
   uv run micro roll app                  # deploy your changes without dropping the Gateway

See :doc:`project` for the layout and ``examples/bot`` for a fuller project
(requests, events, work queues, buttons, a modal, a background task).
