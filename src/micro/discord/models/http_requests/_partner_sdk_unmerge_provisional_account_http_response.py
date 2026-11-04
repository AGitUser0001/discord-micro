# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._partner_sdk_unmerge_provisional_account_http_response_body import PartnerSdkUnmergeProvisionalAccountHTTPResponseBody


class PartnerSdkUnmergeProvisionalAccountHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: PartnerSdkUnmergeProvisionalAccountHTTPResponseBody | None = None
  raw_body: bytes
