# NATS JetStream queue example

This example backs Micro's queue server with durable NATS JetStream. Queue
clients never connect to NATS: the server owns publishing, request/reply,
consumers, acknowledgements, sequence numbers, and redelivery.

Start NATS and install the example:

```console
docker compose up -d nats
uv sync
```

Run the queue ingress:

```console
uv run uvicorn app:queue --port 8200
```

Run a separate competing consumer through the queue server:

```console
uv run consumer.py
```

The actual gateway event router is another ASGI process. It waits for overseer
topology, then uses its `QueueClient` to consume `gateway.events` and forwards
each dispatch once per listening service name:

```console
uv run uvicorn event_service:event_service --port 8201
```

Publish an item through Micro:

```console
curl -i http://127.0.0.1:8200/channels/example.jobs \
  --data-binary 'hello from Micro' \
  -H 'Content-Type: application/octet-stream'
```

Every worker using the durable consumer name `example-worker` shares the work.
The queue responds only after JetStream confirms that it stored the item.

The client-facing API is similarly small:

```python
await service.queue.publish("example.jobs", b"hello from Micro")

delivery = await service.queue.consume("example.jobs", "worker-name")
try:
  await process(delivery.payload)
except Exception:
  await delivery.retry()
else:
  await delivery.acknowledge()

response = await service.queue.request("example.requests", b"question")
```

Request handlers consume normally and finish with `delivery.respond(payload)`.
Run `uv run responder.py` for a minimal responder.
