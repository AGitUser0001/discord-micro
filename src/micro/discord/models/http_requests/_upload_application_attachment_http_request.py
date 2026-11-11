# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http



class UploadApplicationAttachmentHTTPRequest(DiscordModel):
    path: http.UploadApplicationAttachmentParametersPath
    body: http.UploadApplicationAttachmentRequest
    content_type: str = "multipart/form-data"
