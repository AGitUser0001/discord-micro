# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._get_sku_subscription_http_response_body import GetSkuSubscriptionHTTPResponseBody


class GetSkuSubscriptionHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: GetSkuSubscriptionHTTPResponseBody | None = None
    raw_body: bytes
