Application state
=================

Your bot's own state belongs in one of three places, and the right one depends on what the
state is:

* **Records** (warnings, tickets, settings per server, anything you would look up, count or
  list): the **Store**, with ``ctx.store``. Temporary records too: keep an expiry field and look
  at it when you read.
* **Something to happen later** (a reminder, a timeout ending): a **timer**, with ``ctx.timers``
  (:doc:`scheduler`).
* **Something that must run once, not once per replica**: ``service.every`` (:doc:`services`).

Records: the Store
------------------

``ctx.store`` is the real :class:`StoreClient`, so the records live in your own typed schema and
you ask for them with your own queries. Nothing decides what a record looks like for you.

.. code-block:: python

   from micro.store import GraphModule

   WARNINGS = GraphModule(
     id="moderation.warnings",
     schema="""
       type Warning @entity(key: ["guildId", "userId"]) {
         guildId: ID!  userId: ID!  count: Int!
       }
       type Query {
         warning(guildId: ID!, userId: ID!): Warning @from(key: {guildId: guildId, userId: userId})
       }
       type Mutation {
         addWarning(guildId: ID!, userId: ID!): Warning!
           @insert(key: {guildId: guildId, userId: userId},
                   set: {guildId: guildId, userId: userId, count: "1"})
         warn(guildId: ID!, userId: ID!): Warning
           @update(key: {guildId: guildId, userId: userId}, set: {count: "current.count + 1"})
       }
     """,
   )
   service.uses(WARNINGS)                       # the Store process serves it

   await ctx.store.execute('mutation($g: ID!, $u: ID!) { warn(guildId: $g, userId: $u) { count } }',
                           variables={"g": str(guild_id), "u": str(user_id)})

The Store keeps its data on disk, answers queries, and makes the steps of one mutation
all-or-nothing. See :doc:`store` for the schema language.

Buttons do not time out
-----------------------

A discord.py view lives in the process's memory, so it needs a timeout and has to be
re-registered after a restart. A button here carries its own data in its ``custom_id`` and is
routed to whichever replica is alive, so it keeps working across restarts, rolls and scaling.
If a button should stop working after a while, say so in the handler: put a time in the
``custom_id`` data and compare it, or look the id up in the Store.
