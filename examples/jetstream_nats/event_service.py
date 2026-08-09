import os

from micro_nats import JetStreamSource

from micro.gateway import GatewayEventService

event_service = GatewayEventService(
  source=JetStreamSource(
    (os.environ.get("MICRO_NATS_URL", "nats://127.0.0.1:4222"),),
    channel="gateway.events",
    consumer="micro-gateway-event-service",
  )
)
