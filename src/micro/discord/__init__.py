"""Discord API models, the HTTP worker, and its client (imported on first use)."""

from typing import TYPE_CHECKING

from micro._lazy import exports

if TYPE_CHECKING:
  from micro.discord import filters as filters
  from micro.discord import interactions as interactions
  from micro.discord import invite as invite
  from micro.discord import messages as messages
  from micro.discord import models as models
  from micro.discord import objects as objects
  from micro.discord import routes as routes
  from micro.discord import state as state
  from micro.discord import ui as ui
  from micro.discord.http_operations import HTTP_OPERATIONS as HTTP_OPERATIONS
  from micro.discord.http_operations import DiscordHTTPOperation as DiscordHTTPOperation
  from micro.discord.http_operations import DiscordOperationId as DiscordOperationId
  from micro.discord.http_service import DiscordAPIError as DiscordAPIError
  from micro.discord.http_service import DiscordHTTPClient as DiscordHTTPClient
  from micro.discord.http_service import DiscordHTTPRequest as DiscordHTTPRequest
  from micro.discord.http_service import DiscordHTTPResponse as DiscordHTTPResponse
  from micro.discord.http_service import DiscordHTTPWorker as DiscordHTTPWorker
  from micro.discord.http_service import HTTPEvent as HTTPEvent
  from micro.discord.http_service import RateLimits as RateLimits
  from micro.discord.http_service import partition_key as partition_key
  from micro.discord.http_service import rank_workers as rank_workers
  from micro.discord.http_service import route_key as route_key

__getattr__, __dir__ = exports(
  __name__,
  {
    "filters": ".filters",
    "interactions": ".interactions",
    "invite": ".invite",
    "messages": ".messages",
    "models": ".models",
    "objects": ".objects",
    "routes": ".routes",
    "state": ".state",
    "ui": ".ui",
    "HTTP_OPERATIONS": ".http_operations",
    "DiscordHTTPOperation": ".http_operations",
    "DiscordOperationId": ".http_operations",
    "DiscordAPIError": ".http_service",
    "DiscordHTTPClient": ".http_service",
    "DiscordHTTPRequest": ".http_service",
    "DiscordHTTPResponse": ".http_service",
    "DiscordHTTPWorker": ".http_service",
    "HTTPEvent": ".http_service",
    "RateLimits": ".http_service",
    "partition_key": ".http_service",
    "rank_workers": ".http_service",
    "route_key": ".http_service",
  },
)

__all__ = [
  "HTTP_OPERATIONS",
  "DiscordAPIError",
  "DiscordHTTPClient",
  "DiscordHTTPOperation",
  "DiscordHTTPRequest",
  "DiscordHTTPResponse",
  "DiscordHTTPWorker",
  "DiscordOperationId",
  "HTTPEvent",
  "RateLimits",
  "filters",
  "interactions",
  "messages",
  "models",
  "objects",
  "partition_key",
  "rank_workers",
  "route_key",
  "routes",
  "state",
  "ui",
]
