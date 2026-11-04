# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._application_o_auth2_install_params import ApplicationOAuth2InstallParams


class ApplicationIntegrationTypeConfiguration(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    oauth2_install_params: ApplicationOAuth2InstallParams | None = None
