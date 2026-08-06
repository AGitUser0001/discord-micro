from micro.discord.models import gateway, http


def test_gateway_payload_parses_hello() -> None:
  payload = gateway.GatewayPayload.model_validate(
    {
      "op": 10,
      "d": {"heartbeat_interval": 41_250, "future_field": True},
      "s": None,
      "t": None,
    }
  )

  assert isinstance(payload.root, gateway.GatewayReceivePayload)
  assert isinstance(
    payload.root.root, gateway.GatewayNonDispatchReceivePayload
  )
  hello = payload.root.root.root
  assert isinstance(hello, gateway.GatewayHello)
  assert hello.d.heartbeat_interval == 41_250
  assert hello.d.model_extra == {"future_field": True}


def test_http_models_are_permissive_for_future_discord_fields() -> None:
  assert http.UserResponse.model_config.get("extra") == "allow"


def test_gateway_unions_use_wire_discriminators() -> None:
  assert gateway.GatewaySendPayload.model_fields["root"].discriminator == "op"
  assert gateway.GatewayDispatchPayload.model_fields["root"].discriminator == "t"
