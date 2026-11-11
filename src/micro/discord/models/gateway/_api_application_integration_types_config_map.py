# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_application_integration_type_configuration import APIApplicationIntegrationTypeConfiguration


class APIApplicationIntegrationTypesConfigMap(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    field_0: Annotated[
        APIApplicationIntegrationTypeConfiguration | None, Field(alias='0')
    ] = None
    field_1: Annotated[
        APIApplicationIntegrationTypeConfiguration | None, Field(alias='1')
    ] = None
