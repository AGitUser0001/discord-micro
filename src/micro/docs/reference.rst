Wire reference
==============

All names live in ``micro.subjects``.

Subjects
--------

=====================================================  ==========================================
``micro.req.<request_id>``                             requests (queue group ``<request_id>``)
``micro.evt.<event_id>``                               application events
``micro.discord.dispatch.<EVENT>.<guild or _>``        dispatches from the shard owner
``micro.discord.standby.<EVENT>.<guild or _>``         other connections (projection only)
``micro.discord.interaction.<route>``                  routed interactions
``micro.gateway.connection.<shard>``                   connection lifecycle
``micro.gateway.ctl.<shard>.members|voice``            guild control (shard owner)
``micro.discord.http.<worker>``                        HTTP worker requests
``micro.ratelimit.discord.global``                     global rate-limit broadcast
``micro.work.<queue>``                                 work queue jobs
``micro.node.<deployment>.<node>.scale|roll|ps``        node control (``micro dev scale|roll``)
=====================================================  ==========================================

Routes: ``cmd.<type>.<name>`` for commands; ``cmp.p-<hash>`` and ``mdl.p-<hash>``
for declared custom ID routes (a hash of the route's wire form). A service
advertises them in its presence metadata: ``interactions`` lists its routes, and
``component_patterns`` / ``modal_patterns`` map each route to
``{"kind": "module:Class", "data": ...}``, which the router rebuilds with
``Route.load``. Tokens outside ``[A-Za-z0-9_-]`` are ``%`` + hex.

Streams and consumers
---------------------

* ``MICRO_EVENTS`` (interest): events, dispatches, standby, connections.
  Consumer ``svc_<service>`` per listening service.
* ``MICRO_INTERACTIONS`` (work queue, per-message TTL, dedup by interaction
  ID): consumer ``ix_<route>`` per route.
* ``MICRO_WORK_<QUEUE>`` (work queue): consumer ``work_<queue>``.
* ``MICRO_SCHEDULE`` (limits, one message per subject, message schedules on): a timer
  waits under ``micro.schedule.<key>`` and the server publishes it to
  ``micro.due.<key>`` at its time; consumer ``sched_<name>`` per scheduler.

Buckets
-------

==================  ===================================================================
``micro_presence``  ``<kind>.<id>`` → registration (TTL)
``micro_shards``    ``<generation>.<shard>`` → shard lease (TTL)
``micro_gateway``   ``generation.desired``, ``generation.active``, ``presence``
``micro_locks``     identify gates, ``commands.sync``, application locks
``micro_state``     ``decl.<kind>.<hash>``, ``applied.<kind>.<key>``, ``synced.commands.<scope>``, ``rtcmd.<type>.<name>`` (runtime commands)
==================  ===================================================================

The object store ``micro_payloads`` carries request and reply bodies above the
NATS message limit; the message then has an empty body and a
``Micro-Payload: <object>`` header, and the reader deletes the object.

Headers
-------

``Micro-Status: ok|error`` on replies (error body ``{"code","message","detail"}``),
``Micro-Schema`` on requests, ``Micro-Shard``/``Micro-Generation``/``Micro-Connection``
on dispatches.
