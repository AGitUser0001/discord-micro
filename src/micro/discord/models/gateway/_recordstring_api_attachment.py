# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_attachment import APIAttachment


class RecordstringAPIAttachment(RootModel[dict[str, APIAttachment]]):
    root: dict[str, APIAttachment]
