Timers
======

Do something at a time, and keep the promise across restarts. A timer is a message
the NATS server itself holds until its time (message scheduling, **nats-server 2.12 or
newer**), so it is durable, needs no polling, and does not belong to any process.

.. code-block:: python

   from datetime import datetime, timedelta, UTC
   from micro.scheduler import Timers

   timers = Timers(runtime)       # anywhere with a runtime; `service.client.runtime` in a service

   await timers.event("reminder.42", REMIND, Reminder(user=1), after=3600)
   await timers.job("unban.7", UNBAN, Unban(user=7), at=datetime(2030, 1, 1, tzinfo=UTC))
   await timers.cancel("reminder.42")                  # False if there was nothing
   await timers.pending("unban.")                      # not yet due, soonest first

``event`` publishes the application event when the time comes, exactly as if you had
emitted it then; every service listening for it receives it. ``job`` adds to a work
queue. Both take ``at=`` (a timezone-aware datetime, or epoch seconds) or ``after=``
(seconds or a ``timedelta``). Times in the past fire at once.

A **key** names a timer: scheduling the same key again *replaces* it (move a
countdown, extend a ban), and ``cancel(key)`` removes it. Keys are yours to choose, so
use them as ids (``"unban.<user>"``).

Delivery
--------

Something must pick timers up when they come due: run one ``Scheduler`` component in
any process group.

.. code-block:: toml

   [processes.app]
   components = ["mybot.services.*", "micro.scheduler:Scheduler"]

* Timers that come due while no scheduler is running wait, and are delivered when one
  starts. Restarting everything loses nothing.
* Any number of schedulers may run; each timer is delivered once (a redelivery after
  a crash publishes the same message, which NATS de-duplicates).
* A timer is delivered at least once and, in practice, on time to the second; it is
  not a hard real-time guarantee.
* ``pending`` lists timers not yet due; one that has come due and is waiting for a
  scheduler is no longer listed.

Where timers live
-----------------

Timers are messages in the ``MICRO_SCHEDULE`` stream (limits retention, one message per
subject, message schedules switched on), which is why scheduling a key again replaces the
old timer and cancelling is a purge of that subject. When a timer comes due the NATS server
publishes it onto a ``micro.due.>`` subject; the :class:`Scheduler` has a durable consumer
there, republishes it as the application event or work-queue job, and removes the schedule
message. See :doc:`reference` for the stream and subjects.

Requirements
------------

* **nats-server 2.12 or newer.** Message scheduling does not exist before it; Micro raises
  a clear error when it is missing rather than silently never firing.
* A running :class:`Scheduler` somewhere, as above. The event or job targets must be defined
  (``EventSchema`` / ``WorkQueue``, :doc:`services`).

Reference
---------

.. api::
   micro.scheduler.Timers
   micro.scheduler.Timer
   micro.scheduler.Scheduler
   micro.scheduler.ensure_stream
