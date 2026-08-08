import os

from micro_nats import JetStreamBackend

from micro.queue import Queue

queue = Queue(
  backend=JetStreamBackend((os.environ.get("MICRO_NATS_URL", "nats://127.0.0.1:4222"),))
)
