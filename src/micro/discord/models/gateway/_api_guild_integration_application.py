# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_user import APIUser


class APIGuildIntegrationApplication(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[str, Field(description='The id of the app')]
    name: Annotated[str, Field(description='The name of the app')]
    icon: Annotated[str | None, Field(description='The icon hash of the app')]
    description: Annotated[str, Field(description='The description of the app')]
    bot: Annotated[
        APIUser | None, Field(description='The bot associated with this application')
    ] = None
