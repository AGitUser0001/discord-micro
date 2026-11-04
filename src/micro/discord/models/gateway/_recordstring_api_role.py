# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_role import APIRole


class RecordstringAPIRole(RootModel[dict[str, APIRole]]):
    root: dict[str, APIRole]
