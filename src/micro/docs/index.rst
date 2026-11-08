Micro
=====

Micro builds Discord bots (and other applications) from independently replaceable
microservices. One process runs everything on a small box; the same code spreads over many
processes and machines by configuration. Any part can be scaled, rolled, or replaced live.

**NATS is the only required infrastructure.** There is no coordinator: every component keeps
working while NATS is up. Python 3.14+.

.. code-block:: text

   Discord ⇄ GatewayWorker ─┐                 ┌─ your services + templates
                            ├── NATS (JetStream)
   Discord ⇄ DiscordHTTPWorker┘               └─ optional Store

The docs are organized by thing: one page for each component or concept, with how it behaves
and a reference generated from the code for everything it exports. Start with the
:doc:`quickstart`; use the groups below to find the page for the thing you are using. Names
like :class:`Service` or :meth:`Service.listen` link to their reference entries.

.. toctree::
   :maxdepth: 1
   :caption: Start

   quickstart
   project
   deploy
   upgrades

.. toctree::
   :maxdepth: 1
   :caption: Core

   runtime
   coordination
   config
   services
   middleware
   scheduler
   store
   bridge

.. toctree::
   :maxdepth: 1
   :caption: Discord

   discord
   gateway
   events
   http-worker
   api
   objects
   ui
   cache

.. toctree::
   :maxdepth: 1
   :caption: Interactions

   interactions
   commands
   components
   responding
   runtime-commands
   router
   command-sync
   endpoint

.. toctree::
   :maxdepth: 1
   :caption: Reference

   reference
   errors
   design
