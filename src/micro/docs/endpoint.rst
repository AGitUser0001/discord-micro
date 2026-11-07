HTTP endpoint
=============

Instead of the Gateway, Discord can POST each interaction to a URL you give it in the
developer portal (*Interactions Endpoint URL*). :class:`InteractionEndpoint` is that URL.
Put it where :class:`GatewayWorker` was and nothing else changes: the router, commands,
components, modals, middleware, :doc:`command-sync` and :doc:`runtime-commands` all work as
before, because the endpoint publishes the same ``INTERACTION_CREATE`` message the gateway
would.

.. code-block:: toml

   [processes.http]
   components = ["micro.discord.interactions:InteractionEndpoint"]
   replicas = 2                      # any number, behind one URL
   env = { DISCORD_PUBLIC_KEY = "...", MICRO_HTTP_PORT = "8081" }

Install it with ``pip install "micro[http]"`` (a web server). Signatures are checked in plain
Python (about 4 ms each); the ``accel`` extra adds ``cryptography``, which is then used
automatically and is much faster. Put TLS in front of it (a reverse proxy or tunnel): Discord
only calls ``https`` URLs. The public key is on the application's *General Information* page.

.. list-table::
   :header-rows: 1
   :widths: 22 24 54

   * - Argument
     - Environment
     - Meaning
   * - ``public_key``
     - ``DISCORD_PUBLIC_KEY``
     - The application's public key, in hex. Required.
   * - ``host``
     - ``MICRO_HTTP_HOST``
     - Interface to listen on (default ``127.0.0.1``).
   * - ``port``
     - ``MICRO_HTTP_PORT``
     - Port (default 8081).
   * - ``path``
     -
     - URL path (default ``/interactions``).

What it does
------------

* Every request is checked against the key. A bad signature gets **401**, and Discord's
  verification **PING** gets its PONG.
* A valid interaction is published like a gateway dispatch (with the reply subject in its
  payload) and the request is **held open** until a handler gives its *first* response; that
  response becomes the HTTP reply. The router's "isn't available" fallback replies the same
  way.
* Everything after the first response (follow-ups, edits, deletes) uses Discord's webhook
  endpoints as usual.
* Handlers have Discord's three seconds as ever: ``defer()`` first when unsure. The endpoint
  adds no timeout of its own; if Discord gives up, the disconnect ends the request.

Limits
------

Without the Gateway there are **no events** (``service.listen`` for messages, members and so
on) and no :doc:`cache`. An HTTP-only bot answers commands, components and modals, and that
is all.

Reference
---------

.. api::
   micro.discord.interactions.InteractionEndpoint
