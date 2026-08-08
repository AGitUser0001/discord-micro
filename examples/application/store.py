import os

from database import ApacheAgeExecutor

from micro.store import Store

executor = ApacheAgeExecutor(
  os.environ.get(
    "MICRO_AGE_URL",
    "postgresql://micro:micro@127.0.0.1:5455/micro",
  )
)
store = Store(executor=executor)
