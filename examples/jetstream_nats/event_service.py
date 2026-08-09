import os

from micro_nats import JetStreamGatewayEventSource

from micro.gateway import GatewayEventService

event_service = GatewayEventService(
  source=JetStreamGatewayEventSource(
    (os.environ.get("MICRO_NATS_URL", "nats://127.0.0.1:4222"),)
  )
)
