# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._upload_application_attachment_http_response_body import UploadApplicationAttachmentHTTPResponseBody


class UploadApplicationAttachmentHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: UploadApplicationAttachmentHTTPResponseBody | None = None
    raw_body: bytes
