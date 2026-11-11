# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_team_member import APITeamMember


class APITeam(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    icon: Annotated[
        str | None, Field(description="A hash of the image of the team's icon")
    ]
    id: Annotated[str, Field(description='The unique id of the team')]
    members: Annotated[
        list[APITeamMember], Field(description='The members of the team')
    ]
    name: Annotated[str, Field(description='The name of the team')]
    owner_user_id: Annotated[
        str, Field(description='The user id of the current team owner')
    ]
