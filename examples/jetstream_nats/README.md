# NATS JetStream queue example

This example backs Micro's minimal queue ingress with durable NATS JetStream.
Micro transports only a channel and raw payload; JetStream privately manages
storage acknowledgements, sequence numbers, redelivery, and durable consumers.

Start NATS and install the example:

```console
docker compose up -d nats
uv sync
```

Run the queue ingress:

```console
uv run uvicorn app:queue --port 8200
```

Run a separate competing consumer:

```console
uv run consumer.py
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
```
