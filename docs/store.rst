Store
=====

Optional graph storage, run as an ordinary service; no builtin needs it.

.. code-block:: toml

   [processes.store]
   components = ["micro.store:Store"]     # any number of replicas

By default the store is an embedded, disk-backed, schemaless graph in one
SQLite file (``MICRO_STORE_URL=sqlite:.micro/store.db``): no server, no port, no
Docker. RAM holds only SQLite's page cache; store processes on one machine
share the file. For more, implement ``GraphExecutor`` for your database (Spanner
Graph speaks the ISO GQL Micro compiles to) and pass ``Store(executor=...)``.

Modules
-------

Services declare the graph modules they use; stores serve them.

.. code-block:: python

   from micro.store import GraphModule, StoreClient

   NOTES = GraphModule(id="notes", schema="""
     scalar Bytes
     type Note @entity(key: ["id"]) { id: ID! text: String! file: Bytes }
     type Query {
       note(id: ID!): Note @from(key: {id: id})
       notes(first: Int!, offset: Int!): [Note!]! @scan
     }
     type Mutation {
       addNote(id: ID!, text: String!, file: Bytes): Note!
         @insert(key: {id: id}, set: {id: id, text: text, file: file})
     }
   """)

   service.uses(NOTES)
   result = await StoreClient(runtime).execute('{ note(id: "1") { text } }')

Modules converge across rollouts like commands; a stopped service's modules
are retained, and a module set that fails to compose leaves the last good
graph serving. ``micro add example notes`` is a complete example.

Files
-----

``Bytes`` values are base64 strings; files up to tens of megabytes are fine.
Large values are stored out of line, and requests or replies above the NATS
message limit travel through a NATS object store automatically.

Directives
----------

``@entity(key: [...])`` identity, ``@from`` root lookup, ``@fromActive`` lookup
gated by an owner's active flag, ``@scan`` paginated listing, ``@insert``,
``@update``, ``@delete``, ``@connect``, ``@disconnect``. Install more with
``Store(directives=..., type_directives=...)``. Storage is never inferred:
every root field needs a directive.

Gateway projection
------------------

``micro.gateway.projection:GatewayProjection`` stores every connection's
guilds, channels, roles, members, and more; a disconnected connection never
serves stale reads, and ``DiscordState`` reads it. Run one replica.
