# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._gateway_send_payload import GatewaySendPayload
from ._gateway_receive_payload import GatewayReceivePayload


class GatewayPayload(RootModel[GatewayReceivePayload | GatewaySendPayload]):
    root: GatewayReceivePayload | GatewaySendPayload
