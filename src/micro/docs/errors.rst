Errors
======

Every expected failure in Micro derives from :class:`MicroError`, so ``except MicroError``
catches framework failures without catching your own bugs. Each class also derives from the
closest built-in (``LookupError``, ``TimeoutError``, ``ValueError``, ``RuntimeError``), so
generic handlers keep working.

.. list-table::
   :header-rows: 1
   :widths: 28 22 50

   * - Error
     - Also is
     - When
   * - :class:`RoutingError`
     - ``LookupError``
     - Nobody can receive the request: no service handles that request id, no Discord HTTP
       worker is running, no Gateway worker owns the shard.
   * - :class:`RequestTimeoutError`
     - ``TimeoutError``
     - A request got no reply in time.
   * - :class:`RemoteError`
     - ``RuntimeError``
     - A remote component answered with an error. Has ``target``, ``code``, ``message`` and
       ``detail``.
   * - :class:`ServiceError`
     -
     - Raised by *you* in a handler to return an application error to the caller, who gets a
       :class:`RemoteError` with the same ``code``, ``message`` and ``detail``.
   * - :class:`DrainingError`
     - ``RuntimeError``
     - A component refused new work because it is draining or closed.
   * - :class:`TopologyError`
     - ``ValueError``
     - Declared components or ownership conflict.
   * - :class:`BackendExecutionError`
     - ``RuntimeError``
     - A storage backend (the store's executor) failed to run an operation.
   * - :class:`DiscordAPIError`
     -
     - Discord answered an operation with an error status (:doc:`http-worker`).
   * - :class:`InvalidResponse`, :class:`AlreadyResponded`, :class:`InteractionExpired`
     -
     - An interaction was answered in a way Discord would refuse (:doc:`responding`).
   * - :class:`SyncFailed`
     -
     - Some command scopes could not be updated; the rest were (:doc:`command-sync`).
   * - :class:`LockLost`
     -
     - A held lock was taken over before you finished (:doc:`coordination`).

Error codes
-----------

A :class:`RemoteError`'s ``code`` is either one of the framework's or one a
:class:`ServiceError` set:

.. list-table::
   :header-rows: 1
   :widths: 28 72

   * - Code
     - Meaning
   * - ``invalid_input``
     - The request did not validate against its schema (or a Discord operation's model).
   * - ``invalid_output``
     - The handler's reply did not validate against the output schema.
   * - ``incompatible_schema``
     - Caller and handler disagree about the schema (a rollout in progress).
   * - ``handler_failed``
     - The handler raised something other than a :class:`ServiceError`.
   * - ``draining``
     - The replica is shutting down; try again (another replica will answer).
   * - ``ended_without_reply``
     - Middleware ended the request without setting an output (:doc:`services`).

Results: Discord's refusals as values
-------------------------------------

Everything above is raised. The exception is Discord telling you *no*: missing permission,
the message is gone, DMs are closed. That is not a bug and not a broken system, it is an
ordinary answer from a working bot, so the API methods that are being moved to it return it
as a value, a :class:`Result`: an :class:`Ok` with the value, or an :class:`Err` with the
:class:`DiscordAPIError`.

.. code-block:: python

   from micro.discord import NotFound
   from micro.result import Err, Ok

   match await message.edit(content="hi"):
     case Ok(edited): ...
     case Err(NotFound()): ...                   # deleted meanwhile
     case Err(error): raise error

   sent = (await channel.send("hi")).unwrap()    # abort: raises the original error
   maybe = (await channel.send("hi")).ok()       # the message, or None
   (await message.delete()).ignore(NotFound)     # only "already gone" is fine

Handle it where you need to, or write ``unwrap()`` to let it fail: that raises the original
error, so your generic handler sees exactly what it always saw. Bugs and broken
infrastructure (a bad argument, a limit exceeded, NATS down) are not results; they still
raise. Today the message operations (``/channels/{id}/messages...``) return results; the
rest of the API raises, until this settles.

Reference
---------

.. api::
   micro.result.Ok
   micro.result.Err
   micro.result.Result
   micro.errors.MicroError
   micro.errors.RoutingError
   micro.errors.TopologyError
   micro.errors.BackendExecutionError
   micro.errors.RequestTimeoutError
   micro.errors.DrainingError
   micro.errors.ServiceError
   micro.errors.RemoteError
