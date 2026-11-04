# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._auto_moderation_rule_trigger_type import AutoModerationRuleTriggerType
from ._type4 import Type4
from ._integration_type import IntegrationType


class APIAuditLogOptions(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    auto_moderation_rule_name: Annotated[
        str | None,
        Field(
            description='Name of the Auto Moderation rule that was triggered\n\nPresent from:\n- AUTO_MODERATION_BLOCK_MESSAGE\n- AUTO_MODERATION_FLAG_TO_CHANNEL\n- AUTO_MODERATION_USER_COMMUNICATION_DISABLED\n- AUTO_MODERATION_QUARANTINE_USER'
        ),
    ] = None
    auto_moderation_rule_trigger_type: Annotated[
        AutoModerationRuleTriggerType | None,
        Field(
            description='Trigger type of the Auto Moderation rule that was triggered\n\nPresent from:\n- AUTO_MODERATION_BLOCK_MESSAGE\n- AUTO_MODERATION_FLAG_TO_CHANNEL\n- AUTO_MODERATION_USER_COMMUNICATION_DISABLED\n- AUTO_MODERATION_QUARANTINE_USER'
        ),
    ] = None
    delete_member_days: Annotated[
        str | None,
        Field(
            description='Number of days after which inactive members were kicked\n\nPresent from:\n- MEMBER_PRUNE'
        ),
    ] = None
    members_removed: Annotated[
        str | None,
        Field(
            description='Number of members removed by the prune\n\nPresent from:\n- MEMBER_PRUNE'
        ),
    ] = None
    channel_id: Annotated[
        str | None,
        Field(
            description='Channel in which the entities were targeted\n\nPresent from:\n- MEMBER_MOVE\n- MESSAGE_PIN\n- MESSAGE_UNPIN\n- MESSAGE_DELETE\n- STAGE_INSTANCE_CREATE\n- STAGE_INSTANCE_UPDATE\n- STAGE_INSTANCE_DELETE\n- AUTO_MODERATION_BLOCK_MESSAGE\n- AUTO_MODERATION_FLAG_TO_CHANNEL\n- AUTO_MODERATION_USER_COMMUNICATION_DISABLED\n- AUTO_MODERATION_QUARANTINE_USER\n- VOICE_CHANNEL_STATUS_CREATE\n- VOICE_CHANNEL_STATUS_DELETE'
        ),
    ] = None
    message_id: Annotated[
        str | None,
        Field(
            description='ID of the message that was targeted\n\nPresent from:\n- MESSAGE_PIN\n- MESSAGE_UNPIN'
        ),
    ] = None
    count: Annotated[
        str | None,
        Field(
            description='Number of entities that were targeted\n\nPresent from:\n- MESSAGE_DELETE\n- MESSAGE_BULK_DELETE\n- MEMBER_DISCONNECT\n- MEMBER_MOVE'
        ),
    ] = None
    id: Annotated[
        str | None,
        Field(
            description='ID of the overwritten entity\n\nPresent from:\n- CHANNEL_OVERWRITE_CREATE\n- CHANNEL_OVERWRITE_UPDATE\n- CHANNEL_OVERWRITE_DELETE'
        ),
    ] = None
    type: Annotated[
        Type4 | None,
        Field(
            description='Type of overwritten entity - "0" for "role" or "1" for "member"\n\nPresent from:\n- CHANNEL_OVERWRITE_CREATE\n- CHANNEL_OVERWRITE_UPDATE\n- CHANNEL_OVERWRITE_DELETE\n\nAuditLogOptionsType'
        ),
    ] = None
    role_name: Annotated[
        str | None,
        Field(
            description='Name of the role\n\nPresent from:\n- CHANNEL_OVERWRITE_CREATE\n- CHANNEL_OVERWRITE_UPDATE\n- CHANNEL_OVERWRITE_DELETE\n\n**Present only if the "type" | entry type is "0"**'
        ),
    ] = None
    integration_type: Annotated[
        IntegrationType | None,
        Field(
            description='Type of integration which performed the action\n\nPresent from:\n- MEMBER_KICK\n- MEMBER_ROLE_UPDATE'
        ),
    ] = None
    application_id: Annotated[
        str | None,
        Field(
            description='ID of the app whose permissions were targeted\n\nPresent from:\n- APPLICATION_COMMAND_PERMISSION_UPDATE'
        ),
    ] = None
    status: Annotated[
        str | None,
        Field(
            description='The new voice channel status\n\nPresent from:\n- VOICE_CHANNEL_STATUS_CREATE'
        ),
    ] = None
