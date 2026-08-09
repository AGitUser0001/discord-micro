import asyncio
import os

from micro.queue import QueueClient


async def main() -> None:
  client = QueueClient()
  client.apply_state(
    {
      "revision": 0,
      "queues": [
        {
          "id": "local-queue",
          "base_url": os.environ.get("MICRO_QUEUE_URL", "http://127.0.0.1:8200"),
        }
      ],
    }
  )
  try:
    while True:
      delivery = await client.consume("example.jobs", "example-worker")
      try:
        print(delivery.payload.decode(errors="replace"))
      except Exception:
        await delivery.retry()
        raise
      else:
        await delivery.acknowledge()
  finally:
    await client.aclose()


if __name__ == "__main__":
  try:
    asyncio.run(main())
  except KeyboardInterrupt:
    pass
