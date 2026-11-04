Deploying
=========

micro.toml
----------

.. code-block:: toml

   name = "bot"                       # deployment name (supervisor subjects)
   nats = "nats://127.0.0.1:4222"     # or a list
   jetstream_replicas = 1

   [nats_server]                      # started by `micro up` if NATS is unreachable
   enabled = true
   store_dir = ".micro/nats"

   [processes.gateway]
   components = ["micro.gateway:GatewayWorker"]
   replicas = 2

   [processes.app]
   components = ["mybot.services.*"]
   env = { LOG = "debug" }

Targets: ``package.*`` (every component in the package's modules) or
``module:attribute`` (a component, a list, or a class to instantiate).

CLI
---

.. code-block:: console

   micro init NAME | add service NAME   # see Projects
   micro run mybot.services.* micro.discord:DiscordHTTPWorker   # one process
   micro up [micro.toml]          # whole deployment; restarts crashes, Ctrl-C drains
   micro ps                       # processes and live components
   micro scale app 4
   micro roll app                 # new replica, wait until ready, drain old; repeat
   micro gateway status | shards N | roll | presence idle --activity "..."
   micro commands list | sync | forget TYPE:NAME

HTTP bridge
-----------

``micro.http.HTTPBridge`` serves ``/health/live``, ``/health/ready``,
``/components``, ``POST /requests/{id}``, ``POST /events/{id}``, and Gateway
admin routes. Subclass it or add routes to ``bridge.app``; put it behind your
own auth. ``MICRO_HTTP_HOST``/``MICRO_HTTP_PORT`` configure it.

Memory
------

Imports are lazy: a service process is about 35–40 MB. Group stable services
in one process; give separate processes to ones you roll often.

Containers
----------

Only NATS listens on a port. One container running ``micro up`` is enough on a
single machine; the same components run unchanged under systemd, Docker, k3s,
or MicroK8s.
