import asyncio
import os
from uuid import uuid4

import pytest

micro_nats = pytest.importorskip("micro_nats")
JetStreamBackend = micro_nats.JetStreamBackend

NATS_URL = os.getenv("MICRO_NATS_TEST_URL")
pytestmark = pytest.mark.skipif(
  NATS_URL is None, reason="Set MICRO_NATS_TEST_URL to run JetStream tests."
)


def test_jetstream_instances_share_consumers_redeliver_and_cross_settle() -> None:
  assert NATS_URL is not None
  suffix = uuid4().hex[:12]
  stream = f"MICRO_{suffix.upper()}"
  prefix = f"micro.test.{suffix}"

  async def exercise() -> None:
    first = JetStreamBackend((NATS_URL,), stream=stream, subject_prefix=prefix)
    second = JetStreamBackend((NATS_URL,), stream=stream, subject_prefix=prefix)
    await first.start()
    await second.start()
    try:
      await first.publish("jobs", b"one")
      delivery = await second.consume("jobs", "workers", timeout=2)
      assert delivery is not None and delivery.payload == b"one"
      await first.retry(delivery.receipt)
      redelivered = await first.consume("jobs", "workers", timeout=2)
      assert redelivered is not None and redelivered.payload == b"one"
      await second.acknowledge(redelivered.receipt)
      observation = await first.observe()
      assert observation.connected and observation.consumers == 1

      async def respond() -> None:
        request = await second.consume("rpc", "responders", timeout=2)
        assert request is not None and request.reply is not None
        await second.respond(request.receipt, request.reply, b"answer")

      responder = asyncio.create_task(respond())
      assert await first.request("rpc", b"question", timeout=2) == b"answer"
      await responder
      await second.close()
      await second.start()
      assert (await second.observe()).connected
    finally:
      await first.close()
      await second.close()

    with pytest.raises(RuntimeError, match="has not started"):
      await first.publish("jobs", b"partitioned")

  asyncio.run(exercise())
