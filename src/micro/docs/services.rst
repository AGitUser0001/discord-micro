Services
========

A :class:`Service` is a **feature area**: a name, and the requests it answers, events it
listens for and jobs it works on. **Replicas share the service's name**: start more to
scale, drain old ones to roll. A service is a :doc:`component <runtime>`, so you host it
the same way.

.. code-block:: python

   from pydantic import BaseModel
   from micro.service import EventSchema, RequestSchema, Service, ServiceError, WorkQueue

   class Greeting(BaseModel):
     name: str

   GREET = RequestSchema[Greeting, str](id="example.greet", input=Greeting, output=str)
   GREETED = EventSchema[Greeting](id="example.greeted", payload=Greeting)
   AUDIT = WorkQueue[Greeting]("example.audit", Greeting)

   service = Service("greeter")

``Service(name, *, version="0", concurrency=64, ordered_by_guild=False)``: ``version`` is a
label that appears in presence; ``concurrency`` bounds the handlers a replica runs at once
for requests and each consumer; ``ordered_by_guild`` is described under :doc:`events`.

The three kinds of message
--------------------------

.. list-table::
   :header-rows: 1
   :widths: 18 40 42

   * - Kind
     - Who receives it
     - Use it for
   * - Request
     - One replica of the **one service** that handles that id
     - Asking a question or commanding an action and needing the answer.
   * - Event
     - **Every service** that listens, once each (load-balanced over its replicas)
     - Telling the world something happened.
   * - Work
     - **Exactly one worker** across all services and replicas, whenever one is free
     - Jobs that must happen even if nobody is running yet.

Schemas are the contract: Pydantic types for the input and output, wrapped with an id.
Define them in a small module both sides import, or declare the same shape on each side;
services agree through **validated messages, not shared code**.

Requests
--------

Exactly one replica answers. Requests route by **id**, not by service name, so a request can
move from one service to another without its callers noticing.

.. code-block:: python

   @service.handle(GREET)
   async def greet(request: Greeting) -> str:
     if not request.name:
       raise ServiceError("empty_name", "Say who to greet.", detail={"field": "name"})
     return f"Hello, {request.name}!"

   reply = await service.client.request(GREET, Greeting(name="Ada"), timeout=5)

Callers get :class:`RemoteError` (``code``, ``message``, ``detail``), :class:`RoutingError`
(nobody handles it) or :class:`RequestTimeoutError` (default 5 s for a :class:`Client`; a
``timeout=`` per call overrides it). Framework codes and what raising does are in
:doc:`errors`. A handler that raises anything other than :class:`ServiceError` is
``handler_failed``.

**Compatibility is decided by validation, not by equality.** A request carries a hash of its
schema, but the handler only complains (``incompatible_schema``) if the payload *fails to
validate*. A rolling update that adds an optional field keeps working in both directions.

Events
------

Every listening service receives each event once, load-balanced across its replicas. A
service may have many handlers for one event.

.. code-block:: python

   @service.listen(GREETED)
   async def log(event: Greeting) -> None: ...

   @service.listen(GREETED, when=lambda e: e.name.startswith("A"))
   async def only_a(event: Greeting) -> None: ...

   await service.client.emit(GREETED, Greeting(name="Ada"))

Delivery is **at least once**: if a handler fails the event is redelivered and, on the same
replica, only the handlers that failed run again. Discord dispatches are events too, with
``guild_id=`` and filters; they have their own page, :doc:`events`.

Work queues
-----------

Jobs are kept until exactly one worker finishes them, even if none is running.

.. code-block:: python

   @service.work(AUDIT)
   async def record(job: Greeting) -> None: ...

   await service.client.enqueue(AUDIT, Greeting(name="Ada"))

A failing job is retried with a backoff; raise :class:`Reject` (``micro.runtime``) to drop one
that can never succeed, or :class:`Retry` ``(delay)`` to ask for a specific delay.

Rolling updates and schemas
~~~~~~~~~~~~~~~~~~~~~~~~~~~

An event or job that a replica cannot decode is not discarded straight away. If other live
replicas of the same service run a **different schema version**, it is left for them to take
(retried every second). Once every replica agrees and it still does not decode, it is
rejected and logged.

Middleware
----------

``service.use`` wraps every request, event and job handler. It is the same engine as for
interactions, described, with scopes and examples, in :doc:`middleware`. The service flavor
receives a :class:`Call`:

.. code-block:: python

   import time
   from micro.service import Call

   @service.use
   async def timed(call: Call, next) -> None:
     started = time.monotonic()
     await next()
     print(call.kind, call.key, time.monotonic() - started)

   @service.use("example.admin")
   async def staff_only(call: Call, next, end) -> None:
     if not allowed(call.input):
       call.output = "denied"       # what the caller gets
       return await end()
     await next()

A request that ends without an ``output`` fails with ``ended_without_reply``; a
:class:`ServiceError` raised in middleware reaches the caller like one from a handler. For
events and jobs, ``end()`` counts as handled, and an exception retries as usual.

Calling from outside a service
------------------------------

:class:`Client` is the caller half of a service, for scripts, tests and other components:

.. code-block:: python

   from micro.service import Client

   client = Client(runtime, timeout=5.0)
   await client.request(GREET, Greeting(name="Ada"))
   await client.emit(GREETED, Greeting(name="Ada"))
   await client.enqueue(AUDIT, Greeting(name="Ada"))

Declarations and extensions
---------------------------

``service.declare(kind, key, document)`` publishes a versioned document that converges across
rollouts (:doc:`coordination`); ``service.uses(module)`` declares a graph module for the
:doc:`store`. **Templates** such as ``Commands(service)`` attach with ``service.extend(...)``
(they do it themselves) and implement ``start(service)``, ``stop()`` and ``metadata()``.

Setup and teardown
------------------

A service never needs subclassing. ``startup`` runs once when the service starts, before it takes
any work, and ``shutdown`` once when it closes, after its work has finished:

.. code-block:: python

   @service.startup
   async def setup(ctx: Context) -> None:
     ...                                     # open a connection, warm a cache

   @service.shutdown
   async def teardown(ctx: Context) -> None:
     ...                                     # release what setup opened

A ``shutdown`` handler that raises is logged and the others still run.

Doing something on a schedule
-----------------------------

``every`` runs a handler again and again, like discord.py's ``tasks.loop``:

.. code-block:: python

   @service.every(minutes=5)
   async def refresh(ctx: Context) -> None:
     for guild in await ctx.state.guilds():
       ...

It runs once at start and then an interval after each run ends. It runs on **one replica at a
time** (a lock; the others wait, and one takes over if it goes away), so work that must happen
once is not done once per replica. A run that raises is logged and the next one still happens.
The handler may take ``ctx: Context`` like any other. For a one-off at a moment (a reminder in
an hour, a timeout ending) that must survive restarts, schedule a timer instead (:doc:`scheduler`).

Reference
---------

.. api::
   micro.service.Service
   micro.service.Client
   micro.service.RequestSchema
   micro.service.EventSchema
   micro.service.DispatchSchema
   micro.service.WorkQueue
   micro.service.Call
   micro.service.DuplicateRequestHandlerError
   micro.service.DuplicateWorkHandlerError
   micro.service.EventHandler
   micro.service.EventPredicate
   micro.service.RequestHandler
