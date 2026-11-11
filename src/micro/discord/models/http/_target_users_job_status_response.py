# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._target_users_job_status_types import TargetUsersJobStatusTypes
from ._u_int32_type import UInt32Type


class TargetUsersJobStatusResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    status: Annotated[
        TargetUsersJobStatusTypes,
        Field(description='The status of the job processing the target users.'),
    ]
    total_users: Annotated[
        UInt32Type, Field(description='The total number of users in the provided list.')
    ]
    processed_users: Annotated[
        UInt32Type, Field(description='The number of users processed so far.')
    ]
    created_at: Annotated[
        AwareDatetime | None,
        Field(description='The timestamp when the job was created.'),
    ]
    completed_at: Annotated[
        AwareDatetime | None,
        Field(description='The timestamp when the job was successfully completed.'),
    ]
    error_message: Annotated[
        str | None, Field(description='The error message if the job failed.')
    ]
