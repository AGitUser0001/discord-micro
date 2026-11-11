# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._membership_state import MembershipState
from ._role import Role
from ._api_user import APIUser


class APITeamMember(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    membership_state: Annotated[
        MembershipState, Field(description="The user's membership state on the team")
    ]
    permissions: Annotated[
        list[Literal['*']],
        Field(
            deprecated=True,
            description='Will always be `["*"]`',
            max_length=1,
            min_length=1,
        ),
    ]
    team_id: Annotated[
        str, Field(description='The id of the parent team of which they are a member')
    ]
    user: Annotated[APIUser, Field(description='User object of the team member')]
    role: Annotated[Role, Field(description="The user's role in the team.")]
