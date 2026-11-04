# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class APIRoleTags(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    bot_id: Annotated[
        str | None, Field(description='The id of the bot this role belongs to')
    ] = None
    premium_subscriber: Annotated[
        None, Field(description="Whether this is the guild's premium subscriber role")
    ] = None
    integration_id: Annotated[
        str | None, Field(description='The id of the integration this role belongs to')
    ] = None
    subscription_listing_id: Annotated[
        str | None,
        Field(description="The id of this role's subscription sku and listing"),
    ] = None
    available_for_purchase: Annotated[
        None, Field(description='Whether this role is available for purchase')
    ] = None
    guild_connections: Annotated[
        None, Field(description="Whether this role is a guild's linked role")
    ] = None
