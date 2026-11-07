HTTP bridge
===========

:class:`HTTPBridge` serves a small ASGI app inside a runtime, for the things that live
outside NATS: health probes, load balancer checks, an admin API, scripts that cannot speak
NATS. Run it as a component (it needs ``micro[http]``):

.. code-block:: toml

   [processes.bridge]
   components = ["micro.http:HTTPBridge"]
   env = { MICRO_HTTP_HOST = "0.0.0.0", MICRO_HTTP_PORT = "8080" }

The bridge exposes only what it lists. **Put it behind your own authentication**: it has
none, and its routes can call services and operate the Gateway.

Routes
------

.. list-table::
   :header-rows: 1
   :widths: 38 62

   * - Route
     - What it does
   * - ``GET /health/live``
     - 204 while the process is up (a liveness probe).
   * - ``GET /health/ready``
     - 204 once the runtime is ready, 503 before (a readiness probe).
   * - ``GET /components``
     - Every live component in the deployment, from presence.
   * - ``POST /requests/{request_id}``
     - Forwards a JSON body to a service request and returns the reply.
   * - ``POST /events/{event_id}``
     - Publishes a JSON body as an event.
   * - ``GET /gateway``
     - The Gateway status (generations, shards, owners).
   * - ``PUT /gateway/shards``
     - Changes the shard count (a new generation).
   * - ``POST /gateway/roll``
     - Replaces every connection.
   * - ``PUT /gateway/presence``
     - Sets the bot's presence.

Request errors map to HTTP: ``invalid_input`` and ``incompatible_schema`` are 422,
``handler_failed`` and ``invalid_output`` are 500, a request nobody handles is 503, and an
application ``ServiceError`` is 400 with its code and message.

Changing it
-----------

Subclass it and add routes to ``app`` (a Starlette application) before it starts, or
override ``routes()`` to change the built-in ones. ``host`` and ``port`` come from the
arguments or ``MICRO_HTTP_HOST`` / ``MICRO_HTTP_PORT``.

.. api::
   micro.http.HTTPBridge
