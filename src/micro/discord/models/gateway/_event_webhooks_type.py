# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class EventWebhooksType(StrEnum):
    APPLICATION_AUTHORIZED = 'APPLICATION_AUTHORIZED'
    APPLICATION_DEAUTHORIZED = 'APPLICATION_DEAUTHORIZED'
    ENTITLEMENT_CREATE = 'ENTITLEMENT_CREATE'
    ENTITLEMENT_DELETE = 'ENTITLEMENT_DELETE'
    ENTITLEMENT_UPDATE = 'ENTITLEMENT_UPDATE'
    QUEST_USER_ENROLLMENT = 'QUEST_USER_ENROLLMENT'
