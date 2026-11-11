# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._bot_partner_sdk_unmerge_provisional_account_http_response_body import BotPartnerSdkUnmergeProvisionalAccountHTTPResponseBody


class BotPartnerSdkUnmergeProvisionalAccountHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: BotPartnerSdkUnmergeProvisionalAccountHTTPResponseBody | None = None
    raw_body: bytes
