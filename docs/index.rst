Micro
=====

Micro builds Discord bots (and other applications) from independently
replaceable microservices. One process runs everything on a small box; the
same code spreads over many processes and machines by configuration. Any part
can be scaled, rolled, or replaced live.

**NATS is the only required infrastructure.** There is no coordinator: every
component keeps working while NATS is up. Python 3.14+.

.. code-block:: text

   Discord ⇄ GatewayWorker ─┐                 ┌─ your services + templates
                            ├── NATS (JetStream)
   Discord ⇄ DiscordHTTPWorker┘               └─ optional Store

.. toctree::
   :maxdepth: 1

   quickstart
   runtime
   services
   coordination
   discord
   interactions
   store
   deploy
   upgrades
   reference
   design
