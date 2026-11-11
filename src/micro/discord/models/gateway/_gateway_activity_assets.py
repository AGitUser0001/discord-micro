# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class GatewayActivityAssets(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    large_image: str | None = None
    large_text: Annotated[
        str | None,
        Field(
            description='Text displayed when hovering over the large image of the activity'
        ),
    ] = None
    large_url: Annotated[
        str | None,
        Field(description='URL that is opened when clicking on the large image'),
    ] = None
    small_image: str | None = None
    small_text: Annotated[
        str | None,
        Field(
            description='Text displayed when hovering over the small image of the activity'
        ),
    ] = None
    small_url: Annotated[
        str | None,
        Field(description='URL that is opened when clicking on the small image'),
    ] = None
    invite_cover_image: Annotated[
        str | None, Field(description='Displayed as a banner on a Game Invite.')
    ] = None
