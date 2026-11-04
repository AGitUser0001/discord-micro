# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._list_guild_audit_log_entries_http_response_body import ListGuildAuditLogEntriesHTTPResponseBody


class ListGuildAuditLogEntriesHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: ListGuildAuditLogEntriesHTTPResponseBody | None = None
  raw_body: bytes
