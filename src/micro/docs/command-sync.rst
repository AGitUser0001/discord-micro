Command sync
============

:class:`CommandSync` keeps Discord's application commands equal to what your services
declare. Run it once per deployment, with any number of replicas.

.. code-block:: toml

   [processes.interactions]
   components = ["micro.discord.interactions:CommandSync"]

How a command reaches Discord
-----------------------------

Every service that uses ``Commands`` **declares** its command definitions (the content-hashed
documents of :doc:`coordination`). ``CommandSync`` registers a definition only when **every
live replica that declares it agrees on the same version**:

* a rolling update never registers a half-deployed version, and a rollback never leaves a
  command that no running code handles;
* **stopping a service never unregisters its commands** (it may be restarting); retire one
  explicitly with ``micro commands forget TYPE:NAME``;
* :doc:`runtime-commands` are merged in and applied immediately.

Scopes
------

Commands are registered per **scope**: global, and each guild a command names. Each scope is
replaced with one bulk overwrite, which Discord applies atomically, and only when its hash
changes, under a cluster lock so replicas never fight. Scopes are independent, global first:
a scope Discord refuses (a guild the bot left, for example) is retried with backoff and
reported once, without holding up the others. A command counts as applied only when every
scope it belongs to succeeded.

Drift
-----

A pass trusts its own record of what it last sent, so it does not poll Discord. The
**first pass after CommandSync starts**, and ``micro commands sync``, also compare each scope
with what Discord actually has and repair commands deleted or edited elsewhere (the developer
portal, another tool).

Tools
-----

.. code-block:: console

   micro commands list                 # converged state of every command
   micro commands sync                 # one pass now, verifying against Discord
   micro commands forget 1:ticket      # retire a command (type:name)

:func:`sync_commands` is the function behind a pass, if you need one inside your own code
(hold the :data:`SYNC_LOCK` lock around it). ``CommandSync.synced`` is an event set after
each successful pass, handy in tests.

Reference
---------

.. api::
   micro.discord.interactions.CommandSync
   micro.discord.interactions.SyncFailed
   micro.discord.interactions.sync_commands
   micro.discord.interactions.SYNC_LOCK
