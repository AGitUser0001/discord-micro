import asyncio
import os

import nats
from nats.errors import TimeoutError


async def main() -> None:
  connection = await nats.connect(
    os.environ.get("MICRO_NATS_URL", "nats://127.0.0.1:4222")
  )
  jetstream = connection.jetstream()
  subscription = await jetstream.pull_subscribe(
    "micro.queue.example.jobs",
    durable="example-worker",
    stream="MICRO_QUEUE",
  )
  try:
    while True:
      try:
        messages = await subscription.fetch(batch=32, timeout=1)
      except TimeoutError:
        continue
      for message in messages:
        print(message.data.decode(errors="replace"))
        await message.ack()
  finally:
    await connection.drain()


if __name__ == "__main__":
  try:
    asyncio.run(main())
  except KeyboardInterrupt:
    pass
