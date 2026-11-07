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

Reference
---------

.. api::
   micro.errors.MicroError
   micro.errors.RoutingError
   micro.errors.TopologyError
   micro.errors.BackendExecutionError
   micro.errors.RequestTimeoutError
   micro.errors.DrainingError
   micro.errors.ServiceError
   micro.errors.RemoteError
