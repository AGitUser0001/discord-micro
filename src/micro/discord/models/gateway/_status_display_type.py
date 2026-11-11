# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._status_display_type_enum import StatusDisplayTypeEnum


class StatusDisplayType(RootModel[StatusDisplayTypeEnum | None]):
    root: Annotated[
        StatusDisplayTypeEnum | None,
        Field(
            description="Controls which field is displayed in the user's status text in the member list"
        ),
    ] = None
