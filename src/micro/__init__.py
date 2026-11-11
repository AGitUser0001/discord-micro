"""Micro: a NATS-native framework for Discord bots.

`import micro` is enough to reach everything: `micro.discord.Button`, `micro.service.Service`,
`micro.store.Store`, `micro.runtime.Runtime`. Each part is loaded when you first use it, and
your editor still lists them all. Most bots only need `micro.discord` (see it for the
names Discord code uses).
"""

from typing import TYPE_CHECKING

from micro import _slim
from micro._lazy import exports

_slim.install()

if TYPE_CHECKING:
  from micro import config as config
  from micro import coordination as coordination
  from micro import discord as discord
  from micro import errors as errors
  from micro import gateway as gateway
  from micro import log as log
  from micro import middleware as middleware
  from micro import queue as queue
  from micro import result as result
  from micro import runtime as runtime
  from micro import scaffold as scaffold
  from micro import scheduler as scheduler
  from micro import schemas as schemas
  from micro import service as service
  from micro import store as store
  from micro import subjects as subjects

__getattr__, __dir__ = exports(
  __name__,
  {
    "config": ".config",
    "coordination": ".coordination",
    "discord": ".discord",
    "errors": ".errors",
    "gateway": ".gateway",
    "log": ".log",
    "middleware": ".middleware",
    "queue": ".queue",
    "result": ".result",
    "runtime": ".runtime",
    "scaffold": ".scaffold",
    "scheduler": ".scheduler",
    "schemas": ".schemas",
    "service": ".service",
    "store": ".store",
    "subjects": ".subjects",
  },
)

__all__ = [
  "config",
  "coordination",
  "discord",
  "errors",
  "gateway",
  "log",
  "middleware",
  "queue",
  "result",
  "runtime",
  "scaffold",
  "scheduler",
  "schemas",
  "service",
  "store",
  "subjects",
]
