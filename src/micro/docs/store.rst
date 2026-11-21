Store
=====

A small database that every service shares, with no server to run. You describe your
data in a GraphQL schema, services declare it, and any service can then read and
write it with GraphQL. Optional: nothing in Micro needs it, and you can use your own
database (SQLAlchemy, Redis, ...) inside a service instead. See *When to use it* below.

.. code-block:: toml

   [processes.store]
   components = ["micro.store:Store"]     # in micro.toml, any number of replicas

That is the whole setup. Data lives in one SQLite file, ``.micro/store.db`` (set
``MICRO_STORE_URL=sqlite:/path/to/store.db`` to move it). Store processes on one
machine share the file. For another database, implement ``GraphExecutor`` and pass
``Store(executor=...)``: it runs standard ISO GQL statements, with parameters, inside
serializable transactions, and refuses a second node with the same ``_micro_id`` in a
label (``CONFLICT``). Everything else (maps, upserts, keys) is Micro's, compiled to that.

A first module
--------------

A **module** is a GraphQL schema owned by one service. Here is one for a bot's custom
commands. Read it once; the sections below explain each part.

.. code-block:: python

   from micro.service import Service
   from micro.store import GraphModule, StoreClient

   COMMANDS = GraphModule(
     id="myapp.commands",                # unique across your app
     schema="""
       type Guild @entity(key: ["id"]) {
         id: ID!
         name: String!
         prefix: String
         commands: [Command!]!           # a guild's commands: see Relationships
       }

       type Command @entity(key: ["guildId", "name"]) {
         guildId: ID!
         name: String!
         body: String!
         uses: Int!
       }

       type Query {
         guild(id: ID!): Guild @from(key: {id: id})
         command(guildId: ID!, name: String!): Command
           @from(key: {guildId: guildId, name: name})
       }

       type Mutation {
         addGuild(id: ID!, name: String!, prefix: String): Guild!
           @insert(key: {id: id}, set: {id: id, name: name, prefix: prefix})

         addCommand(guildId: ID!, name: String!, body: String!): Command!
           @insert(key: {guildId: guildId, name: name},
                   set: {guildId: guildId, name: name, body: body, uses: "0"})

         attach(guildId: ID!, name: String!): Boolean
           @connect(fromType: "Guild", fromKey: {id: guildId},
                    toType: "Command", toKey: {guildId: guildId, name: name},
                    field: "commands")

         used(guildId: ID!, name: String!): Command
           @update(key: {guildId: guildId, name: name},
                   set: {uses: "current.uses + 1"})
       }
     """,
   )

   service = Service("commands")
   service.uses(COMMANDS)                # the Store process serves it
   store = StoreClient(service.client)   # or StoreClient(runtime)

   guild, name, body = "1234", "hello", "Hi!"
   (await store.execute(t"""
     mutation {{
       c: addCommand(guildId: {guild}, name: {name}, body: {body}) {{ name }}
       a: attach(guildId: {guild}, name: {name})
     }}
   """)).unwrap()
   data = (await store.execute(
     t"{{ guild(id: {guild}) {{ name commands {{ name uses }} }} }}"
   )).unwrap()
   data["guild"]["commands"]               # [{"name": "hello", "uses": 0}]

A query is a **t-string** (``t"..."``). Each ``{value}`` is sent to the store as a GraphQL
variable, never pasted into the text, so any value is safe, quotes and all. Write it bare
where the value goes (``id: {guild}``, not ``id: "{guild}"``); the store types it from
the argument it is passed to, so there is nothing to declare. The query's own braces are
doubled: ``{{ ... }}``. A query with no values is still a t-string.

``execute`` returns a :class:`Result` (:doc:`errors`): ``Ok(data)`` with the operation's
``data``, or ``Err(StoreError)`` for a bad query or a refused write (see *Errors*). An
operation succeeds or fails whole, so there is never part of the data. It raises only
when the store cannot be reached.

Rules of the schema
-------------------

* **Every stored type is an entity**: ``type Name @entity(key: ["field", ...])``. The key
  is the fields that identify one: ``["id"]``, or ``["guildId", "userId"]`` for a
  per-member record. An entity has **exactly one key**; there are no secondary keys, so
  to find things another way see *Relationships*.
* **Types you can use**: ``String``, ``ID``, ``Boolean``, ``Float``, ``Int``, enums,
  lists of those (``[String!]!``), ``Bytes`` (declare ``scalar Bytes``; values are base64
  strings; files up to tens of megabytes are fine), and any other ``scalar`` you declare
  (a ``scalar DateTime`` is stored and returned as the string you give it).
* **Maps and anything-goes values**: declare ``scalar Map`` and a field ``settings: Map`` holds
  any JSON object (nested maps, lists, numbers, strings), read and written as a plain dict.
  Change one key without rewriting the rest, atomically, with map arithmetic in ``@update``::

     put(id: ID!, patch: Map!): User
       @update(key: {id: id}, set: {settings: "current.settings + $patch"})   # {k: v} sets keys
     drop(id: ID!, keys: [String!]!): User
       @update(key: {id: id}, set: {settings: "current.settings - $keys"})    # removes keys

  A missing map counts as empty. Keys of a map are strings (JSON); you cannot filter on
  what is inside a map, so anything you look things up by belongs in its own field.

  Declare the types and writes are checked: ``labels: Map @map(key: String, value: String)``
  refuses a number as a value, whether the map is written whole or by ``+ $patch`` or
  ``- $keys``. Key and value may each be ``String``, ``ID``, ``Int``, ``Float`` or
  ``Boolean`` (a key is a JSON string that must read as that type: ``"7"`` for ``Int``).
* **``Int`` is 32 bits.** Discord ids (snowflakes) do not fit: use ``ID`` or ``String``
  for them. ``Float`` is exact up to 2^53.
* **Every root field needs a directive.** The store never guesses where something is
  kept: a ``Query`` field is ``@from``, ``@fromActive`` or ``@scan``; a ``Mutation``
  field is ``@insert``, ``@update``, ``@upsert``, ``@delete``, ``@connect`` or
  ``@disconnect``.
* **Arguments and keys.** In ``key: {guildId: guildId, name: name}`` the left side is the
  entity's field and the right side is the *argument of the same field*.

Reading
-------

``@from(key: {...})`` returns one entity by its key, or ``null`` if there is none:

.. code-block:: graphql

   guild(id: ID!): Guild @from(key: {id: id})

``@scan`` lists every entity of a type, a page at a time. It must declare exactly
``first: Int!`` and ``offset: Int!`` (``first`` from 1 to 1000):

.. code-block:: graphql

   allGuilds(first: Int!, offset: Int!): [Guild!]! @scan

.. code-block:: python

   offset = 0
   while True:
     page = (await store.execute(
       t"{{ allGuilds(first: 500, offset: {offset}) {{ id name }} }}"
     )).unwrap()["allGuilds"]
     for guild in page: ...
     if len(page) < 500: break
     offset += 500

Scan order is **stable but arbitrary** (it follows a hash of the key, not the key,
insertion order or any field), so paging never skips or repeats an entity, but do not
sort by it. There is no filtering. For "the commands of one guild", use a
relationship.

``@fromActive`` reads an entity only while its owner is *active*: it returns the
entity if the owner holds it through an edge **and** the owner's boolean field is true,
else ``null``. Use it for data that should vanish from view when a switch turns off,
without deleting it:

.. code-block:: graphql

   type Owner @entity(key: ["id"]) { id: ID!  active: Boolean!  items: [Item!]! }
   item(id: ID!, ownerId: ID!): Item
     @fromActive(key: {id: id}, ownerType: "Owner", ownerKey: {id: ownerId},
                 ownerField: "items", activeField: "active")

Writing
-------

``@insert(key, set)`` creates an entity. Naming an existing key is an error
(``CONFLICT``), so an insert never overwrites. ``set`` must include every key field.

``@update(key, set, where)`` changes fields of an existing entity and returns it, or
``null`` if there is none (or ``where`` is false). **Only the fields in** ``set``
**change**; the rest stay as they are.

``@upsert(key, insert, set)`` changes an entity, creating it first if there is none, and
returns it. A new one starts with its key fields and ``insert``; then ``set`` applies, the
same as ``@update``, whether it was just made or already there. Both are optional:
``@upsert(key: {id: id})`` alone makes sure it exists.

.. code-block:: graphql

   warn(guildId: ID!, userId: ID!): Warning!
     @upsert(key: {guildId: guildId, userId: userId},
             insert: {count: "0"}, set: {count: "current.count + 1"})   # first warn: 1

``@delete(type, key)`` removes an entity and every edge to it. It returns true, or
``null`` if there was none.

.. code-block:: graphql

   removeCommand(guildId: ID!, name: String!): Boolean
     @delete(type: "Command", key: {guildId: guildId, name: name})

**The values in** ``set`` are one of:

* a bare **argument name**: ``set: {body: body}`` stores the argument;
* a **GQL string** (ISO GQL, in quotes): a literal, or an expression over the entity's
  *current* values and the arguments. ``current.field`` is the stored value and
  ``$argument`` an argument:

.. code-block:: graphql

   set: {uses: "0"}                         # a literal (text needs inner quotes: "'hi'")
   set: {enabled: "TRUE"}
   set: {uses: "current.uses + 1"}          # increment, atomically
   set: {score: "current.score + $points"}
   update ... where: "current.enabled = TRUE", set: {...}   # only if still enabled

Plain numbers, ``true`` and ``[]`` are not allowed as ``set`` values: write ``"0"``,
``"TRUE"``, or give the argument a default (``tags: [String!] = []``) and set
``tags: tags``.

**Arguments you do not pass.** In an ``@insert`` the field is left unset (``null``); in an
``@update`` it is left **unchanged**. Pass ``null`` explicitly to clear it:

.. code-block:: python

   (await store.execute(t'mutation {{ editBody(guildId: "1", name: "hi") {{ body }} }}')).unwrap()              # no change
   (await store.execute(t'mutation {{ editBody(guildId: "1", name: "hi", body: null) {{ body }} }}')).unwrap()  # cleared

**One request is one transaction.** Put several mutation fields in one request and they
all happen or none does. They run in order, each seeing what the ones before it wrote, and
each returns its own result as it was right after it ran. The earlier example creates a
command and attaches it to its guild together.

**Several queries, with your code between them, as one transaction.** Write the steps as
an async generator: ``yield`` each query (a t-string) and get its ``data`` back, then
``yield Ok(value)`` to commit or ``yield Err(error)`` to roll back:

.. code-block:: python

   from micro.discord import Err, Ok
   from micro.store import Steps

   async def buy(gid: str, price: int) -> Steps[int, NotEnough]:
     data = yield t"{{ guild(id: {gid}) {{ coins }} }}"
     coins = data["guild"]["coins"]
     if coins < price:
       yield Err(NotEnough(coins))                                  # rolls back
     yield t"mutation {{ setCoins(id: {gid}, coins: {coins - price}) {{ id }} }}"
     yield Ok(coins - price)                                        # commits

   match await ctx.store.transaction(buy, gid, price):
     case Ok(left): ...
     case Err(NotEnough()): ...                                     # yours
     case Err(Conflict()): ...                                      # the store refused a query

Nothing between the first query and the commit is visible to anyone else, and nothing is
kept unless it commits. A query the store refuses ends the transaction (rolled back) and
comes back as the ``Err``; an exception in the steps rolls back and propagates; if the
process dies, the store rolls back once its presence expires. Calling
``ctx.store.execute`` inside the steps raises: yield the query instead.

The transaction holds the store while it runs. With SQLite every other write waits for
it, so await only what the logic needs, and keep slow work (Discord calls, downloads)
before or after it.

Checks
------

``@check`` is a field that runs GQL over its arguments and fails the request when it finds
something (``none:``) or nothing (``some:``), with ``code`` (default ``CONFLICT``) and
``message``. Put it before the writes it guards, in the same request: fields run in order
in one transaction, so a failing check keeps none of the request. It returns ``true``
when it passes.

.. code-block:: graphql

   type Mutation {
     nameFree(scope: ID!, name: String!, id: ID!): Boolean
       @check(none: "MATCH (m:Installation) WHERE m.scope = $scope AND m.name = $name AND m.id <> $id",
              message: "That name is taken in this scope.")
     roomForTag(guild: ID!): Boolean
       @check(none: "MATCH (g:Guild)-[:tags]->(t:Tag) WHERE g.id = $guild RETURN count(t) AS n NEXT FILTER n >= 25",
              message: "A guild has at most 25 tags.")
   }

.. code-block:: python

   match await ctx.store.execute(t"""mutation {{
     nameFree(scope: {scope}, name: {name}, id: {iid})
     addInstallation(id: {iid}, scope: {scope}, name: {name}) {{ id }}
   }}"""):
     case Err(Conflict()): ...   # taken; nothing was written

* Use the schema's names: types as labels, fields as properties, an edge as
  ``-[:field]->`` from the type that has the field, and the field's arguments as
  ``$name``. Micro rewrites them to how they are stored, so a check stays right as the
  schema evolves.
* Nothing extra is stored: a check reads the data as it is.
* A check that scans many rows (the first reads every installation) costs that much each
  time; with SQLite that is fine for thousands.

Relationships
-------------

An entity-typed field is an **edge** to another entity. You make and remove edges with
``@connect`` and ``@disconnect``, and read them by selecting the field:

.. code-block:: graphql

   type Guild   @entity(key: ["id"]) { id: ID!  commands: [Command!]! }
   type Command @entity(key: ["guildId", "name"]) { guildId: ID!  name: String!  guild: Guild }

   attach(guildId: ID!, name: String!): Boolean
     @connect(fromType: "Guild", fromKey: {id: guildId},
              toType: "Command", toKey: {guildId: guildId, name: name},
              field: "commands")

* **Keyed entries (a map of anything to an entity).** ``@connect`` and ``@disconnect`` take an
  optional ``edge: {name: argument}``: the entry's own properties, stored on the edge. The
  same entity can be there under several keys, and ``@disconnect`` with ``edge`` removes only
  the entry with those properties::

     place(guild: ID!, position: Int!, role: ID!): Boolean
       @connect(fromType: "Guild", fromKey: {id: guild}, toType: "Role", toKey: {id: role},
                field: "roleAt", edge: {position: position})

  To read the keys back, make the field's type an **entry type** marked ``@edge(target: ...)``:
  its fields are the edge's properties, and ``target`` is the field that is the entity::

     type Guild  @entity(key: ["id"]) { id: ID!  roleAt: [RoleAt!]! }
     type RoleAt @edge(target: "role") { position: Int!  role: Role! }

     { guild(id: "g") { roleAt { position role { name } } } }
* A list-valued field (``[Command!]!``) holds many; a single-valued one (``guild: Guild``)
  holds one.
* Edges go one way. For both directions, declare both fields and connect both.
* ``@connect`` returns true, or ``null`` if either end does not exist. ``@disconnect``
  removes only the edge. Deleting an entity removes its edges.
* This is how you ask for "everything of this kind that belongs to that guild": give
  the guild a list field and connect each new thing to it. Edge fields take no arguments,
  so they cannot be paged or filtered: for a list that can grow into thousands, see
  *When to use it*.

Errors
------

.. code-block:: python

   from micro.discord import Err, Ok
   from micro.store import Conflict, Unavailable

   match await store.execute(...):
     case Ok(data): ...
     case Err(Conflict()): ...         # the key exists: "already there"
     case Err(Unavailable()): ...      # the store is busy or starting: try again
     case Err(error): raise error      # a mistake in the query, or the backend refused it

   (await store.execute(insert)).ignore(Conflict)   # fine if it was already there

Every error is a ``StoreError`` raised as the subclass for its kind, so ``except Conflict:``
and ``.ignore(Conflict)`` work:

* ``Conflict``: you inserted (or connected) something that exists.
* ``Unavailable``: the store is busy or still starting; it is ``retryable``.
* ``Invalid``: the store's backend refused the statement.
* ``BadQuery``: a mistake in the query itself (a syntax error, an unknown field, a missing
  argument); trying again will not help.

Each has the first error's ``message``, ``code`` (the store's code exactly as it sent it, or
None for ``BadQuery``), ``retryable`` and ``path``, and every error in ``errors``. A code
this version does not know yet arrives as a plain ``StoreError`` that still has it in
``code``.

* A mistake in your query (unknown field, missing argument, a bad enum value, ``first``
  out of range) is an ordinary GraphQL error with a message and a location.
* ``CONFLICT``: you inserted a key that exists. Update it instead, or catch it to mean
  "already there".
* ``UNAVAILABLE`` with ``retryable``: the store is busy or starting; try again.
* Not finding something is **not** an error: reads, updates and deletes return ``null``.

Changing a schema
-----------------

Modules **converge**: a new version is applied only when every running replica of the
service declares it, so a rolling deploy never runs half a schema, and the last good
graph keeps serving if a new one does not compose. Stopping a service keeps its module.
Evolve a schema by *adding*:

* **Adding a field** is safe. Rows written earlier read it as ``null``, even if you
  declared it required (``Int!``), so make new fields nullable, or fill them in.
* **Removing a field** only hides it. The data stays stored, and if you add the field
  back it reappears.
* **Renaming a field or changing its type** is not checked and not migrated. Add a new
  field, fill it, and stop using the old one.

Trying a module without a bot
-----------------------------

.. code-block:: python

   import asyncio
   from micro.store import GraphEngine, GraphModule, GraphQLBody
   from micro.store.sqlite import SQLiteGraph

   async def main() -> None:
     graph = SQLiteGraph("try.db")
     await graph.start()
     engine = GraphEngine(graph)
     await engine.apply_modules([COMMANDS])          # raises if the schema is not valid
     out = await engine.execute(GraphQLBody(
       query='mutation { addGuild(id: "1", name: "Home") { id } }'
     ))
     print(out)
     await graph.close()

   asyncio.run(main())

A schema that does not compose says why (``@insert set must include every entity key
field``, ``@scan fields must declare exactly first: Int! and offset: Int!``, ...).

When to use it
--------------

Good for: settings per guild or user, records you look up by id, counters, simple
per-guild lists, files, and state several services share.

Use your own database (inside a service; a library is just a library) when you need
to search by something other than the key, filter or sort, join across kinds, aggregate,
or page a very large per-guild list. The store has no queries beyond key lookups, scans
and edges, by design.

Files
-----

``Bytes`` fields hold files as base64 strings. Large values are stored out of line,
and requests or replies above the NATS message limit travel through a NATS object
store automatically.

Directive reference
-------------------

==================  ==========================================================================
``@entity``         on a type: ``key: ["field", ...]``, exactly one per type
``@from``           ``key``: one entity by key, or null
``@fromActive``     ``key``, ``ownerType``, ``ownerKey``, ``ownerField``, ``activeField``
``@scan``           a page of every entity; ``first`` (1 to 1000) and ``offset``
``@insert``         ``key``, ``set``: create; ``CONFLICT`` if the key exists
``@update``         ``key``, ``set``, optional ``where``: change fields; null if none
``@upsert``         ``key``, optional ``insert`` and ``set``: create if missing, then change
``@delete``         ``type``, ``key``: remove with its edges
``@connect``        ``fromType``, ``fromKey``, ``toType``, ``toKey``, ``field``: add an edge
``@disconnect``     the same: remove an edge
==================  ==========================================================================

Install more directives with ``Store(directives=..., type_directives=...)``. The
``notes`` package (``micro pkg add builtin/notes``) is a small, complete example.

Reference
---------

The store is a service-side component plus a client. Everything a service normally needs is
:class:`GraphModule` (declare a schema), :class:`StoreClient` (run GraphQL) and
:class:`Store` (the process that serves it).

.. api::
   micro.store.Store
   micro.store.StoreClient
   micro.store.Steps
   micro.store.StoreError
   micro.store.Conflict
   micro.store.Unavailable
   micro.store.Invalid
   micro.store.BadQuery
   micro.store.GraphModule
   micro.store.GraphEngine
   micro.store.GraphExecutor
   micro.store.GraphQLBody
   micro.store.GraphQLRequest
   micro.store.GraphResult
   micro.store.GraphTransaction
   micro.store.GraphStatement
   micro.store.MicroGraph
   micro.store.compose_graph
   micro.store.GraphCompiler
   micro.store.GraphCompositionError
   micro.store.GraphBackendError
   micro.store.sqlite.SQLiteGraph
   micro.store.MAX_PAGE_SIZE
   micro.store.STORE_EXECUTE
   micro.store.STORE_BEGIN

Extending the store with directives
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Install more directives with ``Store(directives=..., type_directives=...)``. These are the
types a directive is written with; the ``notes`` package is a small, complete example.

.. api::
   micro.store.DirectiveMetadata
   micro.store.DirectiveBindContext
   micro.store.DirectiveBinding
   micro.store.DirectiveCompileContext
   micro.store.DirectiveCheck
   micro.store.DirectiveRead
   micro.store.DirectiveResult
   micro.store.TypeDirectiveMetadata
   micro.store.TypeDirectiveBindContext
   micro.store.TypeDirectiveBinding
   micro.store.CompiledOperation
   micro.store.ActiveOwnedLookup
   micro.store.Entity
   micro.store.EntityScan
   micro.store.FromDirective
   micro.store.GraphEntityLayout
   micro.store.GraphLayout
   micro.store.entity_identity
   micro.store.physical_field
   micro.store.physical_path_type
   micro.store.physical_reference
   micro.store.physical_type
   micro.store.MUTATION_DIRECTIVES
   micro.store.CHECK_DIRECTIVE
   micro.store.CheckBinding
   micro.store.CONNECT_DIRECTIVE
   micro.store.DELETE_DIRECTIVE
   micro.store.DISCONNECT_DIRECTIVE
   micro.store.FROM_ACTIVE_DIRECTIVE
   micro.store.INSERT_DIRECTIVE
   micro.store.SCAN_DIRECTIVE
   micro.store.UPDATE_DIRECTIVE
   micro.store.UPSERT_DIRECTIVE
