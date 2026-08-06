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

  assert isinstance(payload.root.root, gateway.GatewayHello)
  assert payload.root.root.d.heartbeat_interval == 41_250
  assert payload.root.root.d.model_extra == {"future_field": True}


def test_http_models_are_permissive_for_future_discord_fields() -> None:
  assert http.UserResponse.model_config.get("extra") == "allow"
