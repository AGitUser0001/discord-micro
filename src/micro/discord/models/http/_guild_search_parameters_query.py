# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._author_type import AuthorType
from ._has_option import HasOption
from ._searchable_embed_type import SearchableEmbedType
from ._snowflake_type import SnowflakeType
from ._sorting_mode import SortingMode
from ._sorting_order import SortingOrder
from ._link_hostname_item import LinkHostnameItem
from ._embed_provider_item import EmbedProviderItem
from ._attachment_extension_item import AttachmentExtensionItem
from ._attachment_filename_item import AttachmentFilenameItem


class GuildSearchParametersQuery(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    sort_by: SortingMode | None = None
    sort_order: SortingOrder | None = None
    content: Annotated[str | None, Field(max_length=1024)] = None
    slop: Annotated[int | None, Field(ge=0, le=100)] = None
    author_id: Annotated[list[SnowflakeType] | None, Field(max_length=100)] = None
    author_type: Annotated[list[AuthorType] | None, Field(max_length=6)] = None
    mentions: Annotated[list[SnowflakeType] | None, Field(max_length=100)] = None
    mentions_role_id: Annotated[list[SnowflakeType] | None, Field(max_length=100)] = (
        None
    )
    replied_to_user_id: Annotated[list[SnowflakeType] | None, Field(max_length=100)] = (
        None
    )
    replied_to_message_id: Annotated[
        list[SnowflakeType] | None, Field(max_length=100)
    ] = None
    mention_everyone: bool | None = None
    min_id: SnowflakeType | None = None
    max_id: SnowflakeType | None = None
    limit: Annotated[int | None, Field(ge=1, le=25)] = None
    offset: Annotated[int | None, Field(ge=0, le=9975)] = None
    has: Annotated[list[HasOption] | None, Field(max_length=18)] = None
    link_hostname: Annotated[list[LinkHostnameItem] | None, Field(max_length=100)] = (
        None
    )
    embed_provider: Annotated[list[EmbedProviderItem] | None, Field(max_length=100)] = (
        None
    )
    embed_type: Annotated[list[SearchableEmbedType] | None, Field(max_length=5)] = None
    attachment_extension: Annotated[
        list[AttachmentExtensionItem] | None, Field(max_length=100)
    ] = None
    attachment_filename: Annotated[
        list[AttachmentFilenameItem] | None, Field(max_length=100)
    ] = None
    pinned: bool | None = None
    include_nsfw: bool | None = None
    channel_id: Annotated[list[SnowflakeType] | None, Field(max_length=500)] = None
