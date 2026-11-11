HTTP workers
============

An **HTTP worker** makes Discord REST calls on behalf of everyone else. Services never
hold the bot token or talk to ``discord.com``; they send a request over NATS and a worker
executes it, tracks the rate limit, and sends Discord's answer back. That is why the
rate limits stay correct when you run many services, many processes, or many machines.

.. code-block:: text

   your handler ──► DiscordHTTPClient ──NATS request──► DiscordHTTPWorker ──► discord.com
                          │ picks the worker that owns the bucket
                          ▼
                 rendezvous hashing over live workers

Start one or more; each registers itself so clients can find it:

.. code-block:: toml

   [processes.http]
   components = ["micro.discord:DiscordHTTPWorker"]
   replicas = 2

.. code-block:: python

   from micro.discord import DiscordHTTPWorker

   await runtime.add(DiscordHTTPWorker(max_attempts=4, concurrency=256))

.. list-table::
   :header-rows: 1
   :widths: 20 22 58

   * - Argument
     - Environment
     - Meaning
   * - ``token``
     - ``DISCORD_TOKEN``
     - The bot token, read from the host. Never stored in NATS.
   * - ``api_url``
     - ``DISCORD_API_URL``
     - Another API with Discord's shape (a proxy, or a fake in tests).
   * - ``max_attempts``
     -
     - Tries per request when Discord answers 429 (default 4, at least 1).
   * - ``concurrency``
     -
     - Requests one worker has in flight at once (default 256).
   * - ``transport``
     -
     - An ``httpx2`` transport, for tests (``httpx2.MockTransport``).
   * - ``name``
     -
     - Component name (default ``discord.http``).

Calling Discord
---------------

:class:`DiscordHTTPClient` is the client. Most code never builds one: ``ctx.api`` (a :class:`Context`) in a
handler, ``DiscordState`` and the helpers in :doc:`api` all use it. It needs a runtime.

.. code-block:: python

   from micro.discord import DiscordHTTPClient

   http = DiscordHTTPClient(runtime)

   message = await http.call(                       # plain JSON parts, decoded JSON back
     "create_message", path={"channel_id": "1"}, body={"content": "hi"}
   )
   api = http.api                                   # one method per operation, typed (see api)

``call(operation, *, path, query, body)`` takes the operation's id (all 242 are in
``HTTP_OPERATIONS``, keyed by id), returns the decoded body, and raises
:class:`DiscordAPIError` for an error status. The worker validates the parts against the
operation's generated request model, so a wrong field name is an ``invalid_input``
error before anything reaches Discord. ``call`` returns untyped JSON; ``api`` returns
the typed response model and validates arguments before sending.

.. code-block:: python

   from micro.discord import DiscordAPIError

   try:
     await http.call("get_guild_member", path={"guild_id": "1", "user_id": "2"})
   except DiscordAPIError as error:
     error.status     # 404
     error.body       # Discord's decoded error body, e.g. {"code": 10007, ...}
     error.response   # the raw DiscordHTTPResponse (status, headers, bytes)

Failures other than Discord's own come as the usual Micro errors: ``RoutingError`` (no
worker is running), ``RequestTimeoutError`` (no answer within the client's ``timeout``,
60 s by default) and ``RemoteError`` (the worker rejected the request: ``invalid_input``,
``handler_failed``).

How requests find their worker
------------------------------

Discord rate limits per *bucket*, and a bucket is scoped by a major parameter: a channel,
a guild or a webhook. The client builds a **partition key** from those ids
(:func:`partition_key`; operations with none are keyed by the operation), ranks the live
workers by **rendezvous hashing** (:func:`rank_workers`) and sends the request to the
first. So:

* all requests touching one channel (or guild, or webhook) go to the same worker, and its
  buckets live **in that worker's memory**; nothing needs to be shared or locked;
* when a worker joins or leaves, only the partitions that it owned move;
* if the chosen worker vanished between a directory update and the call, the next-ranked
  one is tried.

Rate limits
-----------

:class:`RateLimits` is the per-worker state. Before each request the worker waits for its
bucket (and the global limit) to allow it; after each response it reads Discord's
``X-RateLimit-*`` headers to update the bucket. A bucket lets through only what Discord
said remains, counting the requests still on their way; when that is not known (the
route's first request, or a used-up window with no reset time) one request goes ahead and
the rest wait for its answer, so a burst does not come back as a burst of 429s. A route
Discord sends no rate-limit headers for is not held back. On a 429 from Discord it waits the
``Retry-After`` and tries again, up to ``max_attempts`` times, then returns the 429 to the
caller (a ``DiscordAPIError`` with status 429). A *global* 429 is announced on NATS
(``micro.ratelimit.discord.global``) so every worker pauses, not just the one that hit it.
429s that did not come from Discord (no ``Via`` header, e.g. a CDN) are returned
as they are rather than retried.

What is sent again, up to ``max_attempts`` times with a short backoff, follows one rule:
**a request is retried when the failed attempt certainly did nothing, or when doing it
twice is the same as doing it once.**

.. list-table::
   :header-rows: 1
   :widths: 46 18 36

   * - what happened
     - retried
     - why
   * - 429 from Discord
     - always
     - Discord refused it
   * - 502, 503
     - always
     - Discord's edge could not hand it to Discord
   * - no connection (refused, connect timeout)
     - always
     - it never left
   * - 504, or a timeout or dropped connection after sending
     - ``GET``, ``PUT``, ``DELETE`` only
     - it may have been carried out; these are idempotent

A ``POST`` creates something each time, and a ``PATCH`` that adds files adds them each
time, so when their outcome is unknown the error is returned for you to decide.

Errors
------

An error status raises :class:`DiscordAPIError`, as the subclass for its status where
there is one, so you catch what you mean:

.. code-block:: python

   from micro.discord import Forbidden, NotFound

   try:
     await ctx.api.message(channel_id, message_id).delete()   # ctx: Context
   except NotFound:
     pass                      # already gone
   except Forbidden as error:
     await interaction.respond(Draft(f"I can't do that here: {error.message}", ephemeral=True))

``status`` is the HTTP status, ``code`` Discord's own error number (10008 "Unknown
Message", 50013 "Missing Permissions"), ``message`` its description and ``body`` the
whole decoded answer. :class:`BadRequest` is 400, :class:`Unauthorized` 401,
:class:`Forbidden` 403, :class:`NotFound` 404, :class:`RateLimited` a 429 that outlasted
every retry, and :class:`DiscordServerError` any 5xx.

A request may carry an **idempotency key** (``DiscordHTTPRequest.idempotency_key``): the
worker remembers the answer under that key, so a client that retries after a lost reply
gets the original answer instead of acting twice. The memory is per worker.

Uploads and audit-log reasons
-----------------------------

``DiscordHTTPRequest.files`` carries uploads (:class:`DiscordHTTPFile`); the worker sends
the request as multipart, putting JSON-capable operations' other fields in ``payload_json``
the way Discord reads uploads. ``reason`` becomes the ``X-Audit-Log-Reason`` header
(percent-encoded). The typed API and the ref objects fill both in for you (see :doc:`api`).

Watching requests
-----------------

:meth:`DiscordHTTPWorker.hook` calls you after every request the worker makes. It is for
metrics and logs: it sees one worker's traffic, costs nothing when no hook is registered,
and a hook that raises is logged without touching the request.

.. code-block:: python

   worker = DiscordHTTPWorker()
   remove = worker.hook(lambda e: print(e.operation, e.status, f"{e.seconds:.2f}s"))

The callback (sync or ``async``) gets an :class:`HTTPEvent`: ``operation``, ``route``,
``attempt`` (1 for the first try; a retry after a 429 is its own event), ``status`` (``None``
if nothing came back), ``seconds``, ``error`` and ``rate_limited``. ``remove()`` unhooks it.

Rewriting requests
------------------

:meth:`DiscordHTTPWorker.rewrite` is the other direction: it changes or refuses a request
**before** it is sent. It is the place for rules that must hold for every caller in the
deployment: stamp an audit-log reason, strip pings, force ephemeral behavior, block an
operation, redirect a channel.

.. code-block:: python

   def stamp(request):
     return request.model_copy(update={"reason": request.reason or "via Micro"})

   def no_bans(request):
     if request.operation == "ban_user_from_guild":
       raise ValueError("bans are disabled")        # the caller gets invalid_input

   worker.rewrite(stamp)
   worker.rewrite(no_bans)

A rewriter gets the :class:`DiscordHTTPRequest` (``operation``, ``data``, ``files``,
``reason``, ``idempotency_key``) and returns a changed copy, or ``None`` to leave it.
Rewriters run in the order added, each seeing the previous result, **before validation and
before the rate-limit route is chosen**, so changing the operation or its ids is safe.
Raising refuses the request: a ``ValueError`` reaches the caller as ``invalid_input``,
anything else as ``handler_failed``, and nothing is sent. A rewriter runs once per request
(not per 429 retry) and not at all for a request answered from its idempotency key. Like
hooks, rewriters are local to the worker, so register the same ones on every worker.

Reference
---------

.. api::
   micro.discord.DiscordHTTPWorker
   micro.discord.DiscordHTTPClient
   micro.discord.DiscordAPIError
   micro.discord.BadRequest
   micro.discord.Unauthorized
   micro.discord.Forbidden
   micro.discord.NotFound
   micro.discord.RateLimited
   micro.discord.DiscordServerError
   micro.discord.http_service.DiscordHTTPRequest
   micro.discord.http_service.DiscordHTTPResponse
   micro.discord.http_service.DiscordHTTPFile
   micro.discord.http_service.HTTPEvent
   micro.discord.http_service.RateLimits
   micro.discord.http_operations.DiscordHTTPOperation
   micro.discord.http_service.partition_key
   micro.discord.http_service.rank_workers
   micro.discord.http_service.route_key
   micro.discord.http_operations.HTTP_OPERATIONS
   micro.discord.http_operations.DiscordOperationId
