Services
========

A ``Service`` is a feature area. Replicas share its name: start more to scale,
drain old ones to roll.

.. code-block:: python

   from pydantic import BaseModel
   from micro.service import EventSchema, RequestSchema, Service, ServiceError, WorkQueue

   class Greeting(BaseModel):
     name: str

   GREET = RequestSchema[Greeting, str](id="example.greet", input=Greeting, output=str)
   GREETED = EventSchema[Greeting](id="example.greeted", payload=Greeting)
   AUDIT = WorkQueue[Greeting]("example.audit", Greeting)

   service = Service("greeter")

Requests
--------

Exactly one replica of one service answers. Errors carry codes.

.. code-block:: python

   @service.handle(GREET)
   async def greet(request: Greeting) -> str:
     if not request.name:
       raise ServiceError("empty_name", "Say who to greet.", detail={"field": "name"})
     return f"Hello, {request.name}!"

   reply = await service.client.request(GREET, Greeting(name="Ada"), timeout=5)

Callers get ``RemoteError`` (``code``, ``message``, ``detail``), ``RoutingError``
(nobody handles it), or ``RequestTimeoutError``. Framework codes:
``invalid_input``, ``incompatible_schema``, ``invalid_output``, ``handler_failed``.

Events
------

Every listening service receives each event once, load-balanced across its
replicas. A service may have many handlers per event.

.. code-block:: python

   @service.listen(GREETED)
   async def log(event: Greeting) -> None: ...

   @service.listen(GREETED, when=lambda e: e.name.startswith("A"))
   async def only_a(event: Greeting) -> None: ...

   await service.client.emit(GREETED, Greeting(name="Ada"))

Delivery is at least once. If a handler fails, the event is redelivered and,
on the same replica, only the failed handlers run again. Events nobody listens
to are dropped. Discord dispatches use ``guild_id=`` (filtered by NATS):

.. code-block:: python

   from micro.schemas import events

   @service.listen(events.MESSAGE_CREATE, guild_id=1234)
   async def on_message(message) -> None: ...

``Service("x", ordered_by_guild=True)`` runs one guild's events one at a time,
in order, within a replica.

Work queues
-----------

Jobs are kept until exactly one worker finishes them, even if none is running.

.. code-block:: python

   @service.work(AUDIT)
   async def record(job: Greeting) -> None: ...

   await service.client.enqueue(AUDIT, Greeting(name="Ada"))

Outside a service
-----------------

.. code-block:: python

   from micro.service import Client
   client = Client(runtime)    # request, emit, enqueue

Declarations and extensions
---------------------------

``service.declare(kind, key, document)`` publishes a versioned document that
converges across rollouts (see :doc:`coordination`); ``service.uses(module)``
declares a graph module. Templates attach with ``service.extend(...)`` (they
do it themselves) and implement ``start(service)``, ``stop()``, ``metadata()``.
