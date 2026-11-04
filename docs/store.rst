Store
=====

Optional graph storage, run as an ordinary service. No builtin needs it.

.. code-block:: python

   from micro.store import GraphModule, Store, StoreClient

   PEOPLE = GraphModule(id="people", schema="""
     type Person @entity(key: ["name"]) { name: String! }
     type Query { person(name: String!): Person @from(key: {name: name}) }
     type Mutation {
       createPerson(name: String!): Person! @insert(key: {name: name}, set: {name: name})
     }
   """)

   store = Store(ApacheAgeExecutor(url), modules=[PEOPLE])   # or let services declare
   service.uses(PEOPLE)

   result = await StoreClient(runtime).execute('{ person(name: "Ada") { name } }')

Modules converge across rollouts like commands; a stopped service's modules
are retained, and a module set that fails to compose leaves the last good
graph serving.

Directives
----------

``@entity(key: [...])`` identity, ``@from`` root lookup, ``@fromActive`` lookup
gated by an owner's active flag, ``@scan`` paginated listing, ``@insert``,
``@update``, ``@delete``, ``@connect``, ``@disconnect``. Install more with
``Store(directives=..., type_directives=...)``. Storage is never inferred:
every root field needs a directive. Operations compile to ISO GQL; physical
names are deterministic hashes, and layouts evolve additively.

Apache AGE
----------

``examples/apache_age`` provides ``ApacheAgeExecutor``:

.. code-block:: console

   docker compose -f examples/apache_age/compose.yaml up --build -d age
   micro run store:store micro.http:HTTPBridge

Gateway projection
------------------

``GatewayProjection`` (``micro.gateway.projection``) stores every connection's
guilds, channels, roles, members, and more, connection-scoped; a disconnected
connection never serves stale reads. Run one replica.
