# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._gateway_non_dispatch_receive_payload import GatewayNonDispatchReceivePayload
from ._gateway_dispatch_payload import GatewayDispatchPayload


class GatewayReceivePayload(
    RootModel[GatewayDispatchPayload | GatewayNonDispatchReceivePayload]
):
    root: GatewayDispatchPayload | GatewayNonDispatchReceivePayload
