# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_application_install_params import APIApplicationInstallParams


class APIApplicationIntegrationTypeConfiguration(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    oauth2_install_params: APIApplicationInstallParams | None = None
