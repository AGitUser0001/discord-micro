Deploying
=========

micro.toml
----------

.. code-block:: toml

   name = "bot"                       # deployment name (shared by every node)
   nats = "nats://127.0.0.1:4222"     # or a list
   jetstream_replicas = 1

   [nats_server]                      # what `micro server start` runs
   enabled = true
   store_dir = ".micro/nats"

   [processes.gateway]
   components = ["micro.gateway:GatewayWorker"]
   replicas = 2

   [processes.app]
   components = ["services.*"]
   env = { LOG = "debug" }

Targets: ``package.*`` (every component in the package's modules) or
``module:attribute`` (a component, a list, or a class to instantiate).

Running it
----------

``micro dev`` runs your bot on this machine: it is a server, the workers, and the
manager that keeps those workers running. It starts the NATS server if none is
running, starts a worker for every replica of every process group in micro.toml,
restarts the ones that crash, and stops them in order on Ctrl-C. That is all most
projects need.

.. code-block:: console

   micro dev                      # everything described in micro.toml
   micro dev scale app 4          # change a running group's replicas
   micro dev roll app             # new replica, wait until ready, drain the old; repeat
   micro nodes list               # the machines running it, their processes, live components (--json for scripts)

Logs go to stderr at ``INFO`` (``MICRO_LOG_LEVEL`` or ``-v`` changes it; ``-v`` also
shows every HTTP request to Discord) and are
colored when stderr is a terminal. ``NO_COLOR=1`` turns the color off and
``FORCE_COLOR=1`` turns it on (through a pager, say).

The pieces underneath, each also usable on its own:

* **server**: NATS (JetStream on), the only thing that listens on a port.
  ``micro server start`` runs it alone; ``micro server status`` says whether it is
  reachable and which nodes are connected.
* **worker**: one process that connects to the server and hosts components. It is the
  server's pair: ``micro worker app`` hosts a process group from micro.toml until
  Ctrl-C (``micro worker discord app`` hosts two in one process), and ``micro dev``
  starts one for each replica. It reads micro.toml for the NATS address, so on another
  machine ``micro worker app`` joins the same bot. Components work too:
  ``micro worker services.*``. Run one by hand to debug a single service, or under
  systemd, Docker, or Kubernetes when they supervise the processes instead.
* **node**: one machine running ``micro dev``. Name it with ``--name`` (default: the
  hostname) when several machines serve one bot; ``scale`` and ``roll`` take
  ``--node NAME`` when more than one of them runs the group.

For more than one machine, run the server on one (``micro server start``, or any
NATS) and point ``nats`` in micro.toml on the others at it; ``micro dev`` there uses
that server instead of starting one.

.. code-block:: console

   # machine A                        # machines B and C
   micro server start                 micro dev --name b       # [nats] names A
   micro dev --name a                 micro dev --name c

CLI
---

.. code-block:: console

   micro init | docs | invite
   micro services add NAME | list
   micro pkg list | add PACKAGE [NAME] | status | diff | upgrade | forget   # see Projects

   micro dev [-c micro.toml] [--name NAME]
   micro dev scale PROCESS N [--node NAME]
   micro dev roll PROCESS [--node NAME]
   micro nodes list
   micro server start | status
   micro worker app | discord app | mybot.services.* micro.discord:DiscordHTTPWorker

   micro gateway status | shards N | roll | presence idle --activity "..."
   micro commands list | sync | forget TYPE:NAME

A command that needs the server and finds none says so at once.

Stopping: Ctrl-C (or SIGTERM, or closing the terminal) on ``micro dev`` stops the
processes in order: each drains its in-flight work. Press Ctrl-C again to skip the
rest of the draining. ``micro dev`` also stops the server, last, if it started it; a
server you started yourself keeps running. Processes and the server run in their own
sessions, so the terminal's Ctrl-C reaches only ``micro dev``.

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

Only NATS listens on a port. One container running ``micro dev`` is enough on a
single machine. For more, run the server on its own (a unit or container for
``micro server start``, or any NATS) and a ``micro dev`` per machine; the
same components run unchanged under systemd, Docker, k3s, or MicroK8s.
