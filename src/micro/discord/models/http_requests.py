# Generated from Discord's OpenAPI specification. Do not edit directly.

from pydantic import RootModel

from micro.discord._model import DiscordModel

from . import http


class GetMyApplicationHTTPRequest(DiscordModel):
  pass


class GetMyApplicationHTTPResponseBody(
  RootModel[
    http.PrivateApplicationResponse | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class GetMyApplicationHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetMyApplicationHTTPResponseBody | None = None
  raw_body: bytes


class UpdateMyApplicationHTTPRequest(DiscordModel):
  body: http.ApplicationFormPartial
  content_type: str = 'application/json'


class UpdateMyApplicationHTTPResponseBody(
  RootModel[
    http.PrivateApplicationResponse | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class UpdateMyApplicationHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: UpdateMyApplicationHTTPResponseBody | None = None
  raw_body: bytes


class GetApplicationHTTPRequest(DiscordModel):
  path: http.GetApplicationParametersPath


class GetApplicationHTTPResponseBody(
  RootModel[
    http.PrivateApplicationResponse | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class GetApplicationHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetApplicationHTTPResponseBody | None = None
  raw_body: bytes


class UpdateApplicationHTTPRequest(DiscordModel):
  path: http.UpdateApplicationParametersPath
  body: http.ApplicationFormPartial
  content_type: str = 'application/json'


class UpdateApplicationHTTPResponseBody(
  RootModel[
    http.PrivateApplicationResponse | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class UpdateApplicationHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: UpdateApplicationHTTPResponseBody | None = None
  raw_body: bytes


class ApplicationsGetActivityInstanceHTTPRequest(DiscordModel):
  path: http.ApplicationsGetActivityInstanceParametersPath


class ApplicationsGetActivityInstanceHTTPResponseBody(
  RootModel[
    http.EmbeddedActivityInstance | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class ApplicationsGetActivityInstanceHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: ApplicationsGetActivityInstanceHTTPResponseBody | None = None
  raw_body: bytes


class UploadApplicationAttachmentHTTPRequest(DiscordModel):
  path: http.UploadApplicationAttachmentParametersPath
  body: http.UploadApplicationAttachmentRequest
  content_type: str = 'multipart/form-data'


class UploadApplicationAttachmentHTTPResponseBody(
  RootModel[
    http.ActivitiesAttachmentResponse | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class UploadApplicationAttachmentHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: UploadApplicationAttachmentHTTPResponseBody | None = None
  raw_body: bytes


class ListApplicationCommandsHTTPRequest(DiscordModel):
  path: http.ListApplicationCommandsParametersPath
  query: http.ListApplicationCommandsParametersQuery | None = None


class ListApplicationCommandsHTTPResponseBody(
  RootModel[
    http.ListApplicationCommandsResponse200
    | http.RatelimitedResponse
    | http.ErrorResponse
  ]
):
  pass


class ListApplicationCommandsHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: ListApplicationCommandsHTTPResponseBody | None = None
  raw_body: bytes


class CreateApplicationCommandHTTPRequest(DiscordModel):
  path: http.CreateApplicationCommandParametersPath
  body: http.ApplicationCommandCreateRequest
  content_type: str = 'application/json'


class CreateApplicationCommandHTTPResponseBody(
  RootModel[
    http.ApplicationCommandResponse | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class CreateApplicationCommandHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: CreateApplicationCommandHTTPResponseBody | None = None
  raw_body: bytes


class BulkSetApplicationCommandsHTTPRequest(DiscordModel):
  path: http.BulkSetApplicationCommandsParametersPath
  body: http.BulkSetApplicationCommandsRequest
  content_type: str = 'application/json'


class BulkSetApplicationCommandsHTTPResponseBody(
  RootModel[
    http.BulkSetApplicationCommandsResponse200
    | http.RatelimitedResponse
    | http.ErrorResponse
  ]
):
  pass


class BulkSetApplicationCommandsHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: BulkSetApplicationCommandsHTTPResponseBody | None = None
  raw_body: bytes


class DeleteApplicationCommandHTTPRequest(DiscordModel):
  path: http.DeleteApplicationCommandParametersPath


class DeleteApplicationCommandHTTPResponseBody(
  RootModel[http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class DeleteApplicationCommandHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: DeleteApplicationCommandHTTPResponseBody | None = None
  raw_body: bytes


class GetApplicationCommandHTTPRequest(DiscordModel):
  path: http.GetApplicationCommandParametersPath


class GetApplicationCommandHTTPResponseBody(
  RootModel[
    http.ApplicationCommandResponse | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class GetApplicationCommandHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetApplicationCommandHTTPResponseBody | None = None
  raw_body: bytes


class UpdateApplicationCommandHTTPRequest(DiscordModel):
  path: http.UpdateApplicationCommandParametersPath
  body: http.ApplicationCommandPatchRequestPartial
  content_type: str = 'application/json'


class UpdateApplicationCommandHTTPResponseBody(
  RootModel[
    http.ApplicationCommandResponse | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class UpdateApplicationCommandHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: UpdateApplicationCommandHTTPResponseBody | None = None
  raw_body: bytes


class ListApplicationEmojisHTTPRequest(DiscordModel):
  path: http.ListApplicationEmojisParametersPath


class ListApplicationEmojisHTTPResponseBody(
  RootModel[
    http.ListApplicationEmojisResponse | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class ListApplicationEmojisHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: ListApplicationEmojisHTTPResponseBody | None = None
  raw_body: bytes


class CreateApplicationEmojiHTTPRequest(DiscordModel):
  path: http.CreateApplicationEmojiParametersPath
  body: http.CreateApplicationEmojiRequest
  content_type: str = 'application/json'


class CreateApplicationEmojiHTTPResponseBody(
  RootModel[http.EmojiResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class CreateApplicationEmojiHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: CreateApplicationEmojiHTTPResponseBody | None = None
  raw_body: bytes


class DeleteApplicationEmojiHTTPRequest(DiscordModel):
  path: http.DeleteApplicationEmojiParametersPath


class DeleteApplicationEmojiHTTPResponseBody(
  RootModel[http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class DeleteApplicationEmojiHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: DeleteApplicationEmojiHTTPResponseBody | None = None
  raw_body: bytes


class GetApplicationEmojiHTTPRequest(DiscordModel):
  path: http.GetApplicationEmojiParametersPath


class GetApplicationEmojiHTTPResponseBody(
  RootModel[http.EmojiResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class GetApplicationEmojiHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetApplicationEmojiHTTPResponseBody | None = None
  raw_body: bytes


class UpdateApplicationEmojiHTTPRequest(DiscordModel):
  path: http.UpdateApplicationEmojiParametersPath
  body: http.UpdateApplicationEmojiRequest
  content_type: str = 'application/json'


class UpdateApplicationEmojiHTTPResponseBody(
  RootModel[http.EmojiResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class UpdateApplicationEmojiHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: UpdateApplicationEmojiHTTPResponseBody | None = None
  raw_body: bytes


class GetEntitlementsHTTPRequest(DiscordModel):
  path: http.GetEntitlementsParametersPath
  query: http.GetEntitlementsParametersQuery | None = None


class GetEntitlementsHTTPResponseBody(
  RootModel[
    http.GetEntitlementsResponse200 | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class GetEntitlementsHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetEntitlementsHTTPResponseBody | None = None
  raw_body: bytes


class CreateEntitlementHTTPRequest(DiscordModel):
  path: http.CreateEntitlementParametersPath
  body: http.CreateEntitlementRequestData
  content_type: str = 'application/json'


class CreateEntitlementHTTPResponseBody(
  RootModel[http.EntitlementResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class CreateEntitlementHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: CreateEntitlementHTTPResponseBody | None = None
  raw_body: bytes


class DeleteEntitlementHTTPRequest(DiscordModel):
  path: http.DeleteEntitlementParametersPath


class DeleteEntitlementHTTPResponseBody(
  RootModel[http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class DeleteEntitlementHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: DeleteEntitlementHTTPResponseBody | None = None
  raw_body: bytes


class GetEntitlementHTTPRequest(DiscordModel):
  path: http.GetEntitlementParametersPath


class GetEntitlementHTTPResponseBody(
  RootModel[http.EntitlementResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class GetEntitlementHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetEntitlementHTTPResponseBody | None = None
  raw_body: bytes


class ConsumeEntitlementHTTPRequest(DiscordModel):
  path: http.ConsumeEntitlementParametersPath


class ConsumeEntitlementHTTPResponseBody(
  RootModel[http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class ConsumeEntitlementHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: ConsumeEntitlementHTTPResponseBody | None = None
  raw_body: bytes


class ListGuildApplicationCommandsHTTPRequest(DiscordModel):
  path: http.ListGuildApplicationCommandsParametersPath
  query: http.ListGuildApplicationCommandsParametersQuery | None = None


class ListGuildApplicationCommandsHTTPResponseBody(
  RootModel[
    http.ListGuildApplicationCommandsResponse200
    | http.RatelimitedResponse
    | http.ErrorResponse
  ]
):
  pass


class ListGuildApplicationCommandsHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: ListGuildApplicationCommandsHTTPResponseBody | None = None
  raw_body: bytes


class CreateGuildApplicationCommandHTTPRequest(DiscordModel):
  path: http.CreateGuildApplicationCommandParametersPath
  body: http.ApplicationCommandCreateRequest
  content_type: str = 'application/json'


class CreateGuildApplicationCommandHTTPResponseBody(
  RootModel[
    http.ApplicationCommandResponse | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class CreateGuildApplicationCommandHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: CreateGuildApplicationCommandHTTPResponseBody | None = None
  raw_body: bytes


class BulkSetGuildApplicationCommandsHTTPRequest(DiscordModel):
  path: http.BulkSetGuildApplicationCommandsParametersPath
  body: http.BulkSetGuildApplicationCommandsRequest
  content_type: str = 'application/json'


class BulkSetGuildApplicationCommandsHTTPResponseBody(
  RootModel[
    http.BulkSetGuildApplicationCommandsResponse200
    | http.RatelimitedResponse
    | http.ErrorResponse
  ]
):
  pass


class BulkSetGuildApplicationCommandsHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: BulkSetGuildApplicationCommandsHTTPResponseBody | None = None
  raw_body: bytes


class ListGuildApplicationCommandPermissionsHTTPRequest(DiscordModel):
  path: http.ListGuildApplicationCommandPermissionsParametersPath


class ListGuildApplicationCommandPermissionsHTTPResponseBody(
  RootModel[
    http.ListGuildApplicationCommandPermissionsResponse200
    | http.RatelimitedResponse
    | http.ErrorResponse
  ]
):
  pass


class ListGuildApplicationCommandPermissionsHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: ListGuildApplicationCommandPermissionsHTTPResponseBody | None = None
  raw_body: bytes


class DeleteGuildApplicationCommandHTTPRequest(DiscordModel):
  path: http.DeleteGuildApplicationCommandParametersPath


class DeleteGuildApplicationCommandHTTPResponseBody(
  RootModel[http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class DeleteGuildApplicationCommandHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: DeleteGuildApplicationCommandHTTPResponseBody | None = None
  raw_body: bytes


class GetGuildApplicationCommandHTTPRequest(DiscordModel):
  path: http.GetGuildApplicationCommandParametersPath


class GetGuildApplicationCommandHTTPResponseBody(
  RootModel[
    http.ApplicationCommandResponse | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class GetGuildApplicationCommandHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetGuildApplicationCommandHTTPResponseBody | None = None
  raw_body: bytes


class UpdateGuildApplicationCommandHTTPRequest(DiscordModel):
  path: http.UpdateGuildApplicationCommandParametersPath
  body: http.ApplicationCommandPatchRequestPartial
  content_type: str = 'application/json'


class UpdateGuildApplicationCommandHTTPResponseBody(
  RootModel[
    http.ApplicationCommandResponse | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class UpdateGuildApplicationCommandHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: UpdateGuildApplicationCommandHTTPResponseBody | None = None
  raw_body: bytes


class GetGuildApplicationCommandPermissionsHTTPRequest(DiscordModel):
  path: http.GetGuildApplicationCommandPermissionsParametersPath


class GetGuildApplicationCommandPermissionsHTTPResponseBody(
  RootModel[
    http.CommandPermissionsResponse | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class GetGuildApplicationCommandPermissionsHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetGuildApplicationCommandPermissionsHTTPResponseBody | None = None
  raw_body: bytes


class SetGuildApplicationCommandPermissionsHTTPRequest(DiscordModel):
  path: http.SetGuildApplicationCommandPermissionsParametersPath
  body: http.SetGuildApplicationCommandPermissionsRequest
  content_type: str = 'application/json'


class SetGuildApplicationCommandPermissionsHTTPResponseBody(
  RootModel[
    http.CommandPermissionsResponse | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class SetGuildApplicationCommandPermissionsHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: SetGuildApplicationCommandPermissionsHTTPResponseBody | None = None
  raw_body: bytes


class GetApplicationRoleConnectionsMetadataHTTPRequest(DiscordModel):
  path: http.GetApplicationRoleConnectionsMetadataParametersPath


class GetApplicationRoleConnectionsMetadataHTTPResponseBody(
  RootModel[
    http.GetApplicationRoleConnectionsMetadataResponse200
    | http.RatelimitedResponse
    | http.ErrorResponse
  ]
):
  pass


class GetApplicationRoleConnectionsMetadataHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetApplicationRoleConnectionsMetadataHTTPResponseBody | None = None
  raw_body: bytes


class UpdateApplicationRoleConnectionsMetadataHTTPRequest(DiscordModel):
  path: http.UpdateApplicationRoleConnectionsMetadataParametersPath
  body: http.UpdateApplicationRoleConnectionsMetadataRequest
  content_type: str = 'application/json'


class UpdateApplicationRoleConnectionsMetadataHTTPResponseBody(
  RootModel[
    http.UpdateApplicationRoleConnectionsMetadataResponse200
    | http.RatelimitedResponse
    | http.ErrorResponse
  ]
):
  pass


class UpdateApplicationRoleConnectionsMetadataHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: UpdateApplicationRoleConnectionsMetadataHTTPResponseBody | None = None
  raw_body: bytes


class DeleteChannelHTTPRequest(DiscordModel):
  path: http.DeleteChannelParametersPath


class DeleteChannelHTTPResponseBody(
  RootModel[
    http.DeleteChannelResponse200 | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class DeleteChannelHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: DeleteChannelHTTPResponseBody | None = None
  raw_body: bytes


class GetChannelHTTPRequest(DiscordModel):
  path: http.GetChannelParametersPath


class GetChannelHTTPResponseBody(
  RootModel[http.GetChannelResponse200 | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class GetChannelHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetChannelHTTPResponseBody | None = None
  raw_body: bytes


class UpdateChannelHTTPRequest(DiscordModel):
  path: http.UpdateChannelParametersPath
  body: http.UpdateChannelRequest
  content_type: str = 'application/json'


class UpdateChannelHTTPResponseBody(
  RootModel[
    http.UpdateChannelResponse200 | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class UpdateChannelHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: UpdateChannelHTTPResponseBody | None = None
  raw_body: bytes


class FollowChannelHTTPRequest(DiscordModel):
  path: http.FollowChannelParametersPath
  body: http.FollowChannelRequest
  content_type: str = 'application/json'


class FollowChannelHTTPResponseBody(
  RootModel[
    http.ChannelFollowerResponse | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class FollowChannelHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: FollowChannelHTTPResponseBody | None = None
  raw_body: bytes


class ListChannelInvitesHTTPRequest(DiscordModel):
  path: http.ListChannelInvitesParametersPath


class ListChannelInvitesHTTPResponseBody(
  RootModel[
    http.ListChannelInvitesResponse200 | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class ListChannelInvitesHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: ListChannelInvitesHTTPResponseBody | None = None
  raw_body: bytes


class CreateChannelInviteHTTPRequest(DiscordModel):
  path: http.CreateChannelInviteParametersPath
  body: http.CreateChannelInviteRequest
  content_type: str = 'application/json'


class CreateChannelInviteHTTPResponseBody(
  RootModel[
    http.CreateChannelInviteResponse200 | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class CreateChannelInviteHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: CreateChannelInviteHTTPResponseBody | None = None
  raw_body: bytes


class ListMessagesHTTPRequest(DiscordModel):
  path: http.ListMessagesParametersPath
  query: http.ListMessagesParametersQuery | None = None


class ListMessagesHTTPResponseBody(
  RootModel[
    http.ListMessagesResponse200 | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class ListMessagesHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: ListMessagesHTTPResponseBody | None = None
  raw_body: bytes


class CreateMessageHTTPRequest(DiscordModel):
  path: http.CreateMessageParametersPath
  body: http.CreateMessageRequest
  content_type: str = 'application/json'


class CreateMessageHTTPResponseBody(
  RootModel[http.MessageResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class CreateMessageHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: CreateMessageHTTPResponseBody | None = None
  raw_body: bytes


class BulkDeleteMessagesHTTPRequest(DiscordModel):
  path: http.BulkDeleteMessagesParametersPath
  body: http.BulkDeleteMessagesRequest
  content_type: str = 'application/json'


class BulkDeleteMessagesHTTPResponseBody(
  RootModel[http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class BulkDeleteMessagesHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: BulkDeleteMessagesHTTPResponseBody | None = None
  raw_body: bytes


class ListPinsHTTPRequest(DiscordModel):
  path: http.ListPinsParametersPath
  query: http.ListPinsParametersQuery | None = None


class ListPinsHTTPResponseBody(
  RootModel[http.PinnedMessagesResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class ListPinsHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: ListPinsHTTPResponseBody | None = None
  raw_body: bytes


class DeletePinHTTPRequest(DiscordModel):
  path: http.DeletePinParametersPath


class DeletePinHTTPResponseBody(
  RootModel[http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class DeletePinHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: DeletePinHTTPResponseBody | None = None
  raw_body: bytes


class CreatePinHTTPRequest(DiscordModel):
  path: http.CreatePinParametersPath


class CreatePinHTTPResponseBody(
  RootModel[http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class CreatePinHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: CreatePinHTTPResponseBody | None = None
  raw_body: bytes


class DeleteMessageHTTPRequest(DiscordModel):
  path: http.DeleteMessageParametersPath


class DeleteMessageHTTPResponseBody(
  RootModel[http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class DeleteMessageHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: DeleteMessageHTTPResponseBody | None = None
  raw_body: bytes


class GetMessageHTTPRequest(DiscordModel):
  path: http.GetMessageParametersPath


class GetMessageHTTPResponseBody(
  RootModel[http.MessageResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class GetMessageHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetMessageHTTPResponseBody | None = None
  raw_body: bytes


class UpdateMessageHTTPRequest(DiscordModel):
  path: http.UpdateMessageParametersPath
  body: http.UpdateMessageRequest
  content_type: str = 'application/json'


class UpdateMessageHTTPResponseBody(
  RootModel[http.MessageResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class UpdateMessageHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: UpdateMessageHTTPResponseBody | None = None
  raw_body: bytes


class CrosspostMessageHTTPRequest(DiscordModel):
  path: http.CrosspostMessageParametersPath


class CrosspostMessageHTTPResponseBody(
  RootModel[http.MessageResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class CrosspostMessageHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: CrosspostMessageHTTPResponseBody | None = None
  raw_body: bytes


class DeleteAllMessageReactionsHTTPRequest(DiscordModel):
  path: http.DeleteAllMessageReactionsParametersPath


class DeleteAllMessageReactionsHTTPResponseBody(
  RootModel[http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class DeleteAllMessageReactionsHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: DeleteAllMessageReactionsHTTPResponseBody | None = None
  raw_body: bytes


class DeleteAllMessageReactionsByEmojiHTTPRequest(DiscordModel):
  path: http.DeleteAllMessageReactionsByEmojiParametersPath


class DeleteAllMessageReactionsByEmojiHTTPResponseBody(
  RootModel[http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class DeleteAllMessageReactionsByEmojiHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: DeleteAllMessageReactionsByEmojiHTTPResponseBody | None = None
  raw_body: bytes


class ListMessageReactionsByEmojiHTTPRequest(DiscordModel):
  path: http.ListMessageReactionsByEmojiParametersPath
  query: http.ListMessageReactionsByEmojiParametersQuery | None = None


class ListMessageReactionsByEmojiHTTPResponseBody(
  RootModel[
    http.ListMessageReactionsByEmojiResponse200
    | http.RatelimitedResponse
    | http.ErrorResponse
  ]
):
  pass


class ListMessageReactionsByEmojiHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: ListMessageReactionsByEmojiHTTPResponseBody | None = None
  raw_body: bytes


class DeleteMyMessageReactionHTTPRequest(DiscordModel):
  path: http.DeleteMyMessageReactionParametersPath


class DeleteMyMessageReactionHTTPResponseBody(
  RootModel[http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class DeleteMyMessageReactionHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: DeleteMyMessageReactionHTTPResponseBody | None = None
  raw_body: bytes


class AddMyMessageReactionHTTPRequest(DiscordModel):
  path: http.AddMyMessageReactionParametersPath


class AddMyMessageReactionHTTPResponseBody(
  RootModel[http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class AddMyMessageReactionHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: AddMyMessageReactionHTTPResponseBody | None = None
  raw_body: bytes


class DeleteUserMessageReactionHTTPRequest(DiscordModel):
  path: http.DeleteUserMessageReactionParametersPath


class DeleteUserMessageReactionHTTPResponseBody(
  RootModel[http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class DeleteUserMessageReactionHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: DeleteUserMessageReactionHTTPResponseBody | None = None
  raw_body: bytes


class CreateThreadFromMessageHTTPRequest(DiscordModel):
  path: http.CreateThreadFromMessageParametersPath
  body: http.CreateTextThreadWithMessageRequest
  content_type: str = 'application/json'


class CreateThreadFromMessageHTTPResponseBody(
  RootModel[http.ThreadResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class CreateThreadFromMessageHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: CreateThreadFromMessageHTTPResponseBody | None = None
  raw_body: bytes


class DeleteChannelPermissionOverwriteHTTPRequest(DiscordModel):
  path: http.DeleteChannelPermissionOverwriteParametersPath


class DeleteChannelPermissionOverwriteHTTPResponseBody(
  RootModel[http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class DeleteChannelPermissionOverwriteHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: DeleteChannelPermissionOverwriteHTTPResponseBody | None = None
  raw_body: bytes


class SetChannelPermissionOverwriteHTTPRequest(DiscordModel):
  path: http.SetChannelPermissionOverwriteParametersPath
  body: http.SetChannelPermissionOverwriteRequest
  content_type: str = 'application/json'


class SetChannelPermissionOverwriteHTTPResponseBody(
  RootModel[http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class SetChannelPermissionOverwriteHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: SetChannelPermissionOverwriteHTTPResponseBody | None = None
  raw_body: bytes


class DeprecatedListPinsHTTPRequest(DiscordModel):
  path: http.DeprecatedListPinsParametersPath


class DeprecatedListPinsHTTPResponseBody(
  RootModel[
    http.DeprecatedListPinsResponse200 | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class DeprecatedListPinsHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: DeprecatedListPinsHTTPResponseBody | None = None
  raw_body: bytes


class DeprecatedDeletePinHTTPRequest(DiscordModel):
  path: http.DeprecatedDeletePinParametersPath


class DeprecatedDeletePinHTTPResponseBody(
  RootModel[http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class DeprecatedDeletePinHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: DeprecatedDeletePinHTTPResponseBody | None = None
  raw_body: bytes


class DeprecatedCreatePinHTTPRequest(DiscordModel):
  path: http.DeprecatedCreatePinParametersPath


class DeprecatedCreatePinHTTPResponseBody(
  RootModel[http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class DeprecatedCreatePinHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: DeprecatedCreatePinHTTPResponseBody | None = None
  raw_body: bytes


class GetAnswerVotersHTTPRequest(DiscordModel):
  path: http.GetAnswerVotersParametersPath
  query: http.GetAnswerVotersParametersQuery | None = None


class GetAnswerVotersHTTPResponseBody(
  RootModel[
    http.PollAnswerDetailsResponse | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class GetAnswerVotersHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetAnswerVotersHTTPResponseBody | None = None
  raw_body: bytes


class PollExpireHTTPRequest(DiscordModel):
  path: http.PollExpireParametersPath


class PollExpireHTTPResponseBody(
  RootModel[http.MessageResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class PollExpireHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: PollExpireHTTPResponseBody | None = None
  raw_body: bytes


class DeleteGroupDmUserHTTPRequest(DiscordModel):
  path: http.DeleteGroupDmUserParametersPath


class DeleteGroupDmUserHTTPResponseBody(
  RootModel[http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class DeleteGroupDmUserHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: DeleteGroupDmUserHTTPResponseBody | None = None
  raw_body: bytes


class AddGroupDmUserHTTPRequest(DiscordModel):
  path: http.AddGroupDmUserParametersPath
  body: http.AddGroupDmUserRequest
  content_type: str = 'application/json'


class AddGroupDmUserHTTPResponseBody(
  RootModel[
    http.AddGroupDmUserResponse201 | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class AddGroupDmUserHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: AddGroupDmUserHTTPResponseBody | None = None
  raw_body: bytes


class SendSoundboardSoundHTTPRequest(DiscordModel):
  path: http.SendSoundboardSoundParametersPath
  body: http.SoundboardSoundSendRequest
  content_type: str = 'application/json'


class SendSoundboardSoundHTTPResponseBody(
  RootModel[http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class SendSoundboardSoundHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: SendSoundboardSoundHTTPResponseBody | None = None
  raw_body: bytes


class ListThreadMembersHTTPRequest(DiscordModel):
  path: http.ListThreadMembersParametersPath
  query: http.ListThreadMembersParametersQuery | None = None


class ListThreadMembersHTTPResponseBody(
  RootModel[
    http.ListThreadMembersResponse200 | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class ListThreadMembersHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: ListThreadMembersHTTPResponseBody | None = None
  raw_body: bytes


class LeaveThreadHTTPRequest(DiscordModel):
  path: http.LeaveThreadParametersPath


class LeaveThreadHTTPResponseBody(
  RootModel[http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class LeaveThreadHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: LeaveThreadHTTPResponseBody | None = None
  raw_body: bytes


class JoinThreadHTTPRequest(DiscordModel):
  path: http.JoinThreadParametersPath


class JoinThreadHTTPResponseBody(
  RootModel[http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class JoinThreadHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: JoinThreadHTTPResponseBody | None = None
  raw_body: bytes


class DeleteThreadMemberHTTPRequest(DiscordModel):
  path: http.DeleteThreadMemberParametersPath


class DeleteThreadMemberHTTPResponseBody(
  RootModel[http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class DeleteThreadMemberHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: DeleteThreadMemberHTTPResponseBody | None = None
  raw_body: bytes


class GetThreadMemberHTTPRequest(DiscordModel):
  path: http.GetThreadMemberParametersPath
  query: http.GetThreadMemberParametersQuery | None = None


class GetThreadMemberHTTPResponseBody(
  RootModel[http.ThreadMemberResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class GetThreadMemberHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetThreadMemberHTTPResponseBody | None = None
  raw_body: bytes


class AddThreadMemberHTTPRequest(DiscordModel):
  path: http.AddThreadMemberParametersPath


class AddThreadMemberHTTPResponseBody(
  RootModel[http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class AddThreadMemberHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: AddThreadMemberHTTPResponseBody | None = None
  raw_body: bytes


class CreateThreadHTTPRequest(DiscordModel):
  path: http.CreateThreadParametersPath
  body: http.CreateThreadRequest
  content_type: str = 'application/json'


class CreateThreadHTTPResponseBody(
  RootModel[http.CreatedThreadResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class CreateThreadHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: CreateThreadHTTPResponseBody | None = None
  raw_body: bytes


class ListPrivateArchivedThreadsHTTPRequest(DiscordModel):
  path: http.ListPrivateArchivedThreadsParametersPath
  query: http.ListPrivateArchivedThreadsParametersQuery | None = None


class ListPrivateArchivedThreadsHTTPResponseBody(
  RootModel[http.ThreadsResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class ListPrivateArchivedThreadsHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: ListPrivateArchivedThreadsHTTPResponseBody | None = None
  raw_body: bytes


class ListPublicArchivedThreadsHTTPRequest(DiscordModel):
  path: http.ListPublicArchivedThreadsParametersPath
  query: http.ListPublicArchivedThreadsParametersQuery | None = None


class ListPublicArchivedThreadsHTTPResponseBody(
  RootModel[http.ThreadsResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class ListPublicArchivedThreadsHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: ListPublicArchivedThreadsHTTPResponseBody | None = None
  raw_body: bytes


class ThreadSearchHTTPRequest(DiscordModel):
  path: http.ThreadSearchParametersPath
  query: http.ThreadSearchParametersQuery | None = None


class ThreadSearchHTTPResponseBody(
  RootModel[
    http.ThreadSearchResponse
    | http.SearchIndexNotReadyResponse
    | http.RatelimitedResponse
    | http.ErrorResponse
  ]
):
  pass


class ThreadSearchHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: ThreadSearchHTTPResponseBody | None = None
  raw_body: bytes


class TriggerTypingIndicatorHTTPRequest(DiscordModel):
  path: http.TriggerTypingIndicatorParametersPath


class TriggerTypingIndicatorHTTPResponseBody(
  RootModel[
    http.TypingIndicatorResponse | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class TriggerTypingIndicatorHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: TriggerTypingIndicatorHTTPResponseBody | None = None
  raw_body: bytes


class ListMyPrivateArchivedThreadsHTTPRequest(DiscordModel):
  path: http.ListMyPrivateArchivedThreadsParametersPath
  query: http.ListMyPrivateArchivedThreadsParametersQuery | None = None


class ListMyPrivateArchivedThreadsHTTPResponseBody(
  RootModel[http.ThreadsResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class ListMyPrivateArchivedThreadsHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: ListMyPrivateArchivedThreadsHTTPResponseBody | None = None
  raw_body: bytes


class UpdateVoiceChannelStatusHTTPRequest(DiscordModel):
  path: http.UpdateVoiceChannelStatusParametersPath
  body: http.UpdateVoiceChannelStatusRequest
  content_type: str = 'application/json'


class UpdateVoiceChannelStatusHTTPResponseBody(
  RootModel[http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class UpdateVoiceChannelStatusHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: UpdateVoiceChannelStatusHTTPResponseBody | None = None
  raw_body: bytes


class ListChannelWebhooksHTTPRequest(DiscordModel):
  path: http.ListChannelWebhooksParametersPath


class ListChannelWebhooksHTTPResponseBody(
  RootModel[
    http.ListChannelWebhooksResponse200 | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class ListChannelWebhooksHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: ListChannelWebhooksHTTPResponseBody | None = None
  raw_body: bytes


class CreateWebhookHTTPRequest(DiscordModel):
  path: http.CreateWebhookParametersPath
  body: http.CreateWebhookRequest
  content_type: str = 'application/json'


class CreateWebhookHTTPResponseBody(
  RootModel[
    http.GuildIncomingWebhookResponse | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class CreateWebhookHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: CreateWebhookHTTPResponseBody | None = None
  raw_body: bytes


class GetGatewayHTTPRequest(DiscordModel):
  pass


class GetGatewayHTTPResponseBody(
  RootModel[http.GatewayResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class GetGatewayHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetGatewayHTTPResponseBody | None = None
  raw_body: bytes


class GetBotGatewayHTTPRequest(DiscordModel):
  pass


class GetBotGatewayHTTPResponseBody(
  RootModel[http.GatewayBotResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class GetBotGatewayHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetBotGatewayHTTPResponseBody | None = None
  raw_body: bytes


class GetGuildTemplateHTTPRequest(DiscordModel):
  path: http.GetGuildTemplateParametersPath


class GetGuildTemplateHTTPResponseBody(
  RootModel[http.GuildTemplateResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class GetGuildTemplateHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetGuildTemplateHTTPResponseBody | None = None
  raw_body: bytes


class GetGuildHTTPRequest(DiscordModel):
  path: http.GetGuildParametersPath
  query: http.GetGuildParametersQuery | None = None


class GetGuildHTTPResponseBody(
  RootModel[
    http.GuildWithCountsResponse | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class GetGuildHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetGuildHTTPResponseBody | None = None
  raw_body: bytes


class UpdateGuildHTTPRequest(DiscordModel):
  path: http.UpdateGuildParametersPath
  body: http.GuildPatchRequestPartial
  content_type: str = 'application/json'


class UpdateGuildHTTPResponseBody(
  RootModel[http.GuildResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class UpdateGuildHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: UpdateGuildHTTPResponseBody | None = None
  raw_body: bytes


class ListGuildAuditLogEntriesHTTPRequest(DiscordModel):
  path: http.ListGuildAuditLogEntriesParametersPath
  query: http.ListGuildAuditLogEntriesParametersQuery | None = None


class ListGuildAuditLogEntriesHTTPResponseBody(
  RootModel[http.GuildAuditLogResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class ListGuildAuditLogEntriesHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: ListGuildAuditLogEntriesHTTPResponseBody | None = None
  raw_body: bytes


class ListAutoModerationRulesHTTPRequest(DiscordModel):
  path: http.ListAutoModerationRulesParametersPath


class ListAutoModerationRulesHTTPResponseBody(
  RootModel[
    http.ListAutoModerationRulesResponse200
    | http.RatelimitedResponse
    | http.ErrorResponse
  ]
):
  pass


class ListAutoModerationRulesHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: ListAutoModerationRulesHTTPResponseBody | None = None
  raw_body: bytes


class CreateAutoModerationRuleHTTPRequest(DiscordModel):
  path: http.CreateAutoModerationRuleParametersPath
  body: http.CreateAutoModerationRuleRequest
  content_type: str = 'application/json'


class CreateAutoModerationRuleHTTPResponseBody(
  RootModel[
    http.CreateAutoModerationRuleResponse200
    | http.RatelimitedResponse
    | http.ErrorResponse
  ]
):
  pass


class CreateAutoModerationRuleHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: CreateAutoModerationRuleHTTPResponseBody | None = None
  raw_body: bytes


class DeleteAutoModerationRuleHTTPRequest(DiscordModel):
  path: http.DeleteAutoModerationRuleParametersPath


class DeleteAutoModerationRuleHTTPResponseBody(
  RootModel[http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class DeleteAutoModerationRuleHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: DeleteAutoModerationRuleHTTPResponseBody | None = None
  raw_body: bytes


class GetAutoModerationRuleHTTPRequest(DiscordModel):
  path: http.GetAutoModerationRuleParametersPath


class GetAutoModerationRuleHTTPResponseBody(
  RootModel[
    http.GetAutoModerationRuleResponse200
    | http.RatelimitedResponse
    | http.ErrorResponse
  ]
):
  pass


class GetAutoModerationRuleHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetAutoModerationRuleHTTPResponseBody | None = None
  raw_body: bytes


class UpdateAutoModerationRuleHTTPRequest(DiscordModel):
  path: http.UpdateAutoModerationRuleParametersPath
  body: http.UpdateAutoModerationRuleRequest
  content_type: str = 'application/json'


class UpdateAutoModerationRuleHTTPResponseBody(
  RootModel[
    http.UpdateAutoModerationRuleResponse200
    | http.RatelimitedResponse
    | http.ErrorResponse
  ]
):
  pass


class UpdateAutoModerationRuleHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: UpdateAutoModerationRuleHTTPResponseBody | None = None
  raw_body: bytes


class ListGuildBansHTTPRequest(DiscordModel):
  path: http.ListGuildBansParametersPath
  query: http.ListGuildBansParametersQuery | None = None


class ListGuildBansHTTPResponseBody(
  RootModel[
    http.ListGuildBansResponse200 | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class ListGuildBansHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: ListGuildBansHTTPResponseBody | None = None
  raw_body: bytes


class UnbanUserFromGuildHTTPRequest(DiscordModel):
  path: http.UnbanUserFromGuildParametersPath
  body: http.UnbanUserFromGuildRequest
  content_type: str = 'application/json'


class UnbanUserFromGuildHTTPResponseBody(
  RootModel[http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class UnbanUserFromGuildHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: UnbanUserFromGuildHTTPResponseBody | None = None
  raw_body: bytes


class GetGuildBanHTTPRequest(DiscordModel):
  path: http.GetGuildBanParametersPath


class GetGuildBanHTTPResponseBody(
  RootModel[http.GuildBanResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class GetGuildBanHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetGuildBanHTTPResponseBody | None = None
  raw_body: bytes


class BanUserFromGuildHTTPRequest(DiscordModel):
  path: http.BanUserFromGuildParametersPath
  body: http.BanUserFromGuildRequest
  content_type: str = 'application/json'


class BanUserFromGuildHTTPResponseBody(
  RootModel[http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class BanUserFromGuildHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: BanUserFromGuildHTTPResponseBody | None = None
  raw_body: bytes


class BulkBanUsersFromGuildHTTPRequest(DiscordModel):
  path: http.BulkBanUsersFromGuildParametersPath
  body: http.BulkBanUsersRequest
  content_type: str = 'application/json'


class BulkBanUsersFromGuildHTTPResponseBody(
  RootModel[http.BulkBanUsersResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class BulkBanUsersFromGuildHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: BulkBanUsersFromGuildHTTPResponseBody | None = None
  raw_body: bytes


class ListGuildChannelsHTTPRequest(DiscordModel):
  path: http.ListGuildChannelsParametersPath


class ListGuildChannelsHTTPResponseBody(
  RootModel[
    http.ListGuildChannelsResponse200 | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class ListGuildChannelsHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: ListGuildChannelsHTTPResponseBody | None = None
  raw_body: bytes


class BulkUpdateGuildChannelsHTTPRequest(DiscordModel):
  path: http.BulkUpdateGuildChannelsParametersPath
  body: http.BulkUpdateGuildChannelsRequest
  content_type: str = 'application/json'


class BulkUpdateGuildChannelsHTTPResponseBody(
  RootModel[http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class BulkUpdateGuildChannelsHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: BulkUpdateGuildChannelsHTTPResponseBody | None = None
  raw_body: bytes


class CreateGuildChannelHTTPRequest(DiscordModel):
  path: http.CreateGuildChannelParametersPath
  body: http.CreateGuildChannelRequest
  content_type: str = 'application/json'


class CreateGuildChannelHTTPResponseBody(
  RootModel[http.GuildChannelResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class CreateGuildChannelHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: CreateGuildChannelHTTPResponseBody | None = None
  raw_body: bytes


class ListGuildEmojisHTTPRequest(DiscordModel):
  path: http.ListGuildEmojisParametersPath


class ListGuildEmojisHTTPResponseBody(
  RootModel[
    http.ListGuildEmojisResponse200 | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class ListGuildEmojisHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: ListGuildEmojisHTTPResponseBody | None = None
  raw_body: bytes


class CreateGuildEmojiHTTPRequest(DiscordModel):
  path: http.CreateGuildEmojiParametersPath
  body: http.CreateGuildEmojiRequest
  content_type: str = 'application/json'


class CreateGuildEmojiHTTPResponseBody(
  RootModel[http.EmojiResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class CreateGuildEmojiHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: CreateGuildEmojiHTTPResponseBody | None = None
  raw_body: bytes


class DeleteGuildEmojiHTTPRequest(DiscordModel):
  path: http.DeleteGuildEmojiParametersPath


class DeleteGuildEmojiHTTPResponseBody(
  RootModel[http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class DeleteGuildEmojiHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: DeleteGuildEmojiHTTPResponseBody | None = None
  raw_body: bytes


class GetGuildEmojiHTTPRequest(DiscordModel):
  path: http.GetGuildEmojiParametersPath


class GetGuildEmojiHTTPResponseBody(
  RootModel[http.EmojiResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class GetGuildEmojiHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetGuildEmojiHTTPResponseBody | None = None
  raw_body: bytes


class UpdateGuildEmojiHTTPRequest(DiscordModel):
  path: http.UpdateGuildEmojiParametersPath
  body: http.UpdateGuildEmojiRequest
  content_type: str = 'application/json'


class UpdateGuildEmojiHTTPResponseBody(
  RootModel[http.EmojiResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class UpdateGuildEmojiHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: UpdateGuildEmojiHTTPResponseBody | None = None
  raw_body: bytes


class UpdateGuildIncidentActionsHTTPRequest(DiscordModel):
  path: http.UpdateGuildIncidentActionsParametersPath
  body: http.GuildIncidentActionsRequest
  content_type: str = 'application/json'


class UpdateGuildIncidentActionsHTTPResponseBody(
  RootModel[
    http.GuildIncidentsDataResponse | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class UpdateGuildIncidentActionsHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: UpdateGuildIncidentActionsHTTPResponseBody | None = None
  raw_body: bytes


class ListGuildIntegrationsHTTPRequest(DiscordModel):
  path: http.ListGuildIntegrationsParametersPath


class ListGuildIntegrationsHTTPResponseBody(
  RootModel[
    http.ListGuildIntegrationsResponse200
    | http.RatelimitedResponse
    | http.ErrorResponse
  ]
):
  pass


class ListGuildIntegrationsHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: ListGuildIntegrationsHTTPResponseBody | None = None
  raw_body: bytes


class DeleteGuildIntegrationHTTPRequest(DiscordModel):
  path: http.DeleteGuildIntegrationParametersPath


class DeleteGuildIntegrationHTTPResponseBody(
  RootModel[http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class DeleteGuildIntegrationHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: DeleteGuildIntegrationHTTPResponseBody | None = None
  raw_body: bytes


class ListGuildInvitesHTTPRequest(DiscordModel):
  path: http.ListGuildInvitesParametersPath


class ListGuildInvitesHTTPResponseBody(
  RootModel[
    http.ListGuildInvitesResponse200 | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class ListGuildInvitesHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: ListGuildInvitesHTTPResponseBody | None = None
  raw_body: bytes


class ListGuildMembersHTTPRequest(DiscordModel):
  path: http.ListGuildMembersParametersPath
  query: http.ListGuildMembersParametersQuery | None = None


class ListGuildMembersHTTPResponseBody(
  RootModel[
    http.ListGuildMembersResponse200 | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class ListGuildMembersHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: ListGuildMembersHTTPResponseBody | None = None
  raw_body: bytes


class UpdateMyGuildMemberHTTPRequest(DiscordModel):
  path: http.UpdateMyGuildMemberParametersPath
  body: http.UpdateMyGuildMemberRequest
  content_type: str = 'application/json'


class UpdateMyGuildMemberHTTPResponseBody(
  RootModel[
    http.PrivateGuildMemberResponse | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class UpdateMyGuildMemberHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: UpdateMyGuildMemberHTTPResponseBody | None = None
  raw_body: bytes


class SearchGuildMembersHTTPRequest(DiscordModel):
  path: http.SearchGuildMembersParametersPath
  query: http.SearchGuildMembersParametersQuery | None = None


class SearchGuildMembersHTTPResponseBody(
  RootModel[
    http.SearchGuildMembersResponse200 | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class SearchGuildMembersHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: SearchGuildMembersHTTPResponseBody | None = None
  raw_body: bytes


class DeleteGuildMemberHTTPRequest(DiscordModel):
  path: http.DeleteGuildMemberParametersPath


class DeleteGuildMemberHTTPResponseBody(
  RootModel[http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class DeleteGuildMemberHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: DeleteGuildMemberHTTPResponseBody | None = None
  raw_body: bytes


class GetGuildMemberHTTPRequest(DiscordModel):
  path: http.GetGuildMemberParametersPath


class GetGuildMemberHTTPResponseBody(
  RootModel[http.GuildMemberResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class GetGuildMemberHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetGuildMemberHTTPResponseBody | None = None
  raw_body: bytes


class UpdateGuildMemberHTTPRequest(DiscordModel):
  path: http.UpdateGuildMemberParametersPath
  body: http.UpdateGuildMemberRequest
  content_type: str = 'application/json'


class UpdateGuildMemberHTTPResponseBody(
  RootModel[http.GuildMemberResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class UpdateGuildMemberHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: UpdateGuildMemberHTTPResponseBody | None = None
  raw_body: bytes


class AddGuildMemberHTTPRequest(DiscordModel):
  path: http.AddGuildMemberParametersPath
  body: http.BotAddGuildMemberRequest
  content_type: str = 'application/json'


class AddGuildMemberHTTPResponseBody(
  RootModel[http.GuildMemberResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class AddGuildMemberHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: AddGuildMemberHTTPResponseBody | None = None
  raw_body: bytes


class DeleteGuildMemberRoleHTTPRequest(DiscordModel):
  path: http.DeleteGuildMemberRoleParametersPath


class DeleteGuildMemberRoleHTTPResponseBody(
  RootModel[http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class DeleteGuildMemberRoleHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: DeleteGuildMemberRoleHTTPResponseBody | None = None
  raw_body: bytes


class AddGuildMemberRoleHTTPRequest(DiscordModel):
  path: http.AddGuildMemberRoleParametersPath


class AddGuildMemberRoleHTTPResponseBody(
  RootModel[http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class AddGuildMemberRoleHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: AddGuildMemberRoleHTTPResponseBody | None = None
  raw_body: bytes


class GuildSearchHTTPRequest(DiscordModel):
  path: http.GuildSearchParametersPath
  query: http.GuildSearchParametersQuery | None = None


class GuildSearchHTTPResponseBody(
  RootModel[
    http.GuildSearchResponse
    | http.SearchIndexNotReadyResponse
    | http.RatelimitedResponse
    | http.ErrorResponse
  ]
):
  pass


class GuildSearchHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GuildSearchHTTPResponseBody | None = None
  raw_body: bytes


class GetGuildNewMemberWelcomeHTTPRequest(DiscordModel):
  path: http.GetGuildNewMemberWelcomeParametersPath


class GetGuildNewMemberWelcomeHTTPResponseBody(
  RootModel[
    http.GuildHomeSettingsResponse | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class GetGuildNewMemberWelcomeHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetGuildNewMemberWelcomeHTTPResponseBody | None = None
  raw_body: bytes


class GetGuildsOnboardingHTTPRequest(DiscordModel):
  path: http.GetGuildsOnboardingParametersPath


class GetGuildsOnboardingHTTPResponseBody(
  RootModel[
    http.UserGuildOnboardingResponse | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class GetGuildsOnboardingHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetGuildsOnboardingHTTPResponseBody | None = None
  raw_body: bytes


class PutGuildsOnboardingHTTPRequest(DiscordModel):
  path: http.PutGuildsOnboardingParametersPath
  body: http.UpdateGuildOnboardingRequest
  content_type: str = 'application/json'


class PutGuildsOnboardingHTTPResponseBody(
  RootModel[
    http.GuildOnboardingResponse | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class PutGuildsOnboardingHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: PutGuildsOnboardingHTTPResponseBody | None = None
  raw_body: bytes


class GetGuildPreviewHTTPRequest(DiscordModel):
  path: http.GetGuildPreviewParametersPath


class GetGuildPreviewHTTPResponseBody(
  RootModel[http.GuildPreviewResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class GetGuildPreviewHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetGuildPreviewHTTPResponseBody | None = None
  raw_body: bytes


class PreviewPruneGuildHTTPRequest(DiscordModel):
  path: http.PreviewPruneGuildParametersPath
  query: http.PreviewPruneGuildParametersQuery | None = None


class PreviewPruneGuildHTTPResponseBody(
  RootModel[http.GuildPruneResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class PreviewPruneGuildHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: PreviewPruneGuildHTTPResponseBody | None = None
  raw_body: bytes


class PruneGuildHTTPRequest(DiscordModel):
  path: http.PruneGuildParametersPath
  body: http.PruneGuildRequest
  content_type: str = 'application/json'


class PruneGuildHTTPResponseBody(
  RootModel[http.GuildPruneResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class PruneGuildHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: PruneGuildHTTPResponseBody | None = None
  raw_body: bytes


class ListGuildVoiceRegionsHTTPRequest(DiscordModel):
  path: http.ListGuildVoiceRegionsParametersPath


class ListGuildVoiceRegionsHTTPResponseBody(
  RootModel[
    http.ListGuildVoiceRegionsResponse200
    | http.RatelimitedResponse
    | http.ErrorResponse
  ]
):
  pass


class ListGuildVoiceRegionsHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: ListGuildVoiceRegionsHTTPResponseBody | None = None
  raw_body: bytes


class GetGuildJoinRequestsHTTPRequest(DiscordModel):
  path: http.GetGuildJoinRequestsParametersPath
  query: http.GetGuildJoinRequestsParametersQuery | None = None


class GetGuildJoinRequestsHTTPResponseBody(
  RootModel[
    http.GuildJoinRequestsListResponse | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class GetGuildJoinRequestsHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetGuildJoinRequestsHTTPResponseBody | None = None
  raw_body: bytes


class ActionGuildJoinRequestHTTPRequest(DiscordModel):
  path: http.ActionGuildJoinRequestParametersPath
  body: http.ActionGuildJoinRequestRequest
  content_type: str = 'application/json'


class ActionGuildJoinRequestHTTPResponseBody(
  RootModel[
    http.GuildJoinRequestResponse | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class ActionGuildJoinRequestHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: ActionGuildJoinRequestHTTPResponseBody | None = None
  raw_body: bytes


class ListGuildRolesHTTPRequest(DiscordModel):
  path: http.ListGuildRolesParametersPath


class ListGuildRolesHTTPResponseBody(
  RootModel[
    http.ListGuildRolesResponse200 | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class ListGuildRolesHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: ListGuildRolesHTTPResponseBody | None = None
  raw_body: bytes


class BulkUpdateGuildRolesHTTPRequest(DiscordModel):
  path: http.BulkUpdateGuildRolesParametersPath
  body: http.BulkUpdateGuildRolesRequest
  content_type: str = 'application/json'


class BulkUpdateGuildRolesHTTPResponseBody(
  RootModel[
    http.BulkUpdateGuildRolesResponse200 | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class BulkUpdateGuildRolesHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: BulkUpdateGuildRolesHTTPResponseBody | None = None
  raw_body: bytes


class CreateGuildRoleHTTPRequest(DiscordModel):
  path: http.CreateGuildRoleParametersPath
  body: http.CreateRoleRequest
  content_type: str = 'application/json'


class CreateGuildRoleHTTPResponseBody(
  RootModel[http.GuildRoleResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class CreateGuildRoleHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: CreateGuildRoleHTTPResponseBody | None = None
  raw_body: bytes


class GuildRoleMemberCountsHTTPRequest(DiscordModel):
  path: http.GuildRoleMemberCountsParametersPath


class GuildRoleMemberCountsHTTPResponseBody(
  RootModel[
    http.GuildRoleMemberCountsResponse200
    | http.RatelimitedResponse
    | http.ErrorResponse
  ]
):
  pass


class GuildRoleMemberCountsHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GuildRoleMemberCountsHTTPResponseBody | None = None
  raw_body: bytes


class DeleteGuildRoleHTTPRequest(DiscordModel):
  path: http.DeleteGuildRoleParametersPath


class DeleteGuildRoleHTTPResponseBody(
  RootModel[http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class DeleteGuildRoleHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: DeleteGuildRoleHTTPResponseBody | None = None
  raw_body: bytes


class GetGuildRoleHTTPRequest(DiscordModel):
  path: http.GetGuildRoleParametersPath


class GetGuildRoleHTTPResponseBody(
  RootModel[http.GuildRoleResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class GetGuildRoleHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetGuildRoleHTTPResponseBody | None = None
  raw_body: bytes


class UpdateGuildRoleHTTPRequest(DiscordModel):
  path: http.UpdateGuildRoleParametersPath
  body: http.UpdateRoleRequestPartial
  content_type: str = 'application/json'


class UpdateGuildRoleHTTPResponseBody(
  RootModel[http.GuildRoleResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class UpdateGuildRoleHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: UpdateGuildRoleHTTPResponseBody | None = None
  raw_body: bytes


class ListGuildScheduledEventsHTTPRequest(DiscordModel):
  path: http.ListGuildScheduledEventsParametersPath
  query: http.ListGuildScheduledEventsParametersQuery | None = None


class ListGuildScheduledEventsHTTPResponseBody(
  RootModel[
    http.ListGuildScheduledEventsResponse200
    | http.RatelimitedResponse
    | http.ErrorResponse
  ]
):
  pass


class ListGuildScheduledEventsHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: ListGuildScheduledEventsHTTPResponseBody | None = None
  raw_body: bytes


class CreateGuildScheduledEventHTTPRequest(DiscordModel):
  path: http.CreateGuildScheduledEventParametersPath
  body: http.CreateGuildScheduledEventRequest
  content_type: str = 'application/json'


class CreateGuildScheduledEventHTTPResponseBody(
  RootModel[
    http.CreateGuildScheduledEventResponse200
    | http.RatelimitedResponse
    | http.ErrorResponse
  ]
):
  pass


class CreateGuildScheduledEventHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: CreateGuildScheduledEventHTTPResponseBody | None = None
  raw_body: bytes


class DeleteGuildScheduledEventHTTPRequest(DiscordModel):
  path: http.DeleteGuildScheduledEventParametersPath


class DeleteGuildScheduledEventHTTPResponseBody(
  RootModel[http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class DeleteGuildScheduledEventHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: DeleteGuildScheduledEventHTTPResponseBody | None = None
  raw_body: bytes


class GetGuildScheduledEventHTTPRequest(DiscordModel):
  path: http.GetGuildScheduledEventParametersPath
  query: http.GetGuildScheduledEventParametersQuery | None = None


class GetGuildScheduledEventHTTPResponseBody(
  RootModel[
    http.GetGuildScheduledEventResponse200
    | http.RatelimitedResponse
    | http.ErrorResponse
  ]
):
  pass


class GetGuildScheduledEventHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetGuildScheduledEventHTTPResponseBody | None = None
  raw_body: bytes


class UpdateGuildScheduledEventHTTPRequest(DiscordModel):
  path: http.UpdateGuildScheduledEventParametersPath
  body: http.UpdateGuildScheduledEventRequest
  content_type: str = 'application/json'


class UpdateGuildScheduledEventHTTPResponseBody(
  RootModel[
    http.UpdateGuildScheduledEventResponse200
    | http.RatelimitedResponse
    | http.ErrorResponse
  ]
):
  pass


class UpdateGuildScheduledEventHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: UpdateGuildScheduledEventHTTPResponseBody | None = None
  raw_body: bytes


class CreateGuildScheduledEventExceptionHTTPRequest(DiscordModel):
  path: http.CreateGuildScheduledEventExceptionParametersPath
  body: http.GuildScheduledEventExceptionCreateRequest
  content_type: str = 'application/json'


class CreateGuildScheduledEventExceptionHTTPResponseBody(
  RootModel[
    http.GuildScheduledEventExceptionResponse
    | http.RatelimitedResponse
    | http.ErrorResponse
  ]
):
  pass


class CreateGuildScheduledEventExceptionHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: CreateGuildScheduledEventExceptionHTTPResponseBody | None = None
  raw_body: bytes


class DeleteGuildScheduledEventExceptionHTTPRequest(DiscordModel):
  path: http.DeleteGuildScheduledEventExceptionParametersPath


class DeleteGuildScheduledEventExceptionHTTPResponseBody(
  RootModel[http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class DeleteGuildScheduledEventExceptionHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: DeleteGuildScheduledEventExceptionHTTPResponseBody | None = None
  raw_body: bytes


class UpdateGuildScheduledEventExceptionHTTPRequest(DiscordModel):
  path: http.UpdateGuildScheduledEventExceptionParametersPath
  body: http.GuildScheduledEventExceptionPatchRequestPartial
  content_type: str = 'application/json'


class UpdateGuildScheduledEventExceptionHTTPResponseBody(
  RootModel[
    http.GuildScheduledEventExceptionResponse
    | http.RatelimitedResponse
    | http.ErrorResponse
  ]
):
  pass


class UpdateGuildScheduledEventExceptionHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: UpdateGuildScheduledEventExceptionHTTPResponseBody | None = None
  raw_body: bytes


class ListGuildScheduledEventUsersHTTPRequest(DiscordModel):
  path: http.ListGuildScheduledEventUsersParametersPath
  query: http.ListGuildScheduledEventUsersParametersQuery | None = None


class ListGuildScheduledEventUsersHTTPResponseBody(
  RootModel[
    http.ListGuildScheduledEventUsersResponse200
    | http.RatelimitedResponse
    | http.ErrorResponse
  ]
):
  pass


class ListGuildScheduledEventUsersHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: ListGuildScheduledEventUsersHTTPResponseBody | None = None
  raw_body: bytes


class CountGuildScheduledEventUsersHTTPRequest(DiscordModel):
  path: http.CountGuildScheduledEventUsersParametersPath
  query: http.CountGuildScheduledEventUsersParametersQuery | None = None


class CountGuildScheduledEventUsersHTTPResponseBody(
  RootModel[
    http.ScheduledEventUserCountResponse | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class CountGuildScheduledEventUsersHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: CountGuildScheduledEventUsersHTTPResponseBody | None = None
  raw_body: bytes


class ListGuildScheduledEventExceptionUsersHTTPRequest(DiscordModel):
  path: http.ListGuildScheduledEventExceptionUsersParametersPath
  query: http.ListGuildScheduledEventExceptionUsersParametersQuery | None = None


class ListGuildScheduledEventExceptionUsersHTTPResponseBody(
  RootModel[
    http.ListGuildScheduledEventExceptionUsersResponse200
    | http.RatelimitedResponse
    | http.ErrorResponse
  ]
):
  pass


class ListGuildScheduledEventExceptionUsersHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: ListGuildScheduledEventExceptionUsersHTTPResponseBody | None = None
  raw_body: bytes


class ListGuildSoundboardSoundsHTTPRequest(DiscordModel):
  path: http.ListGuildSoundboardSoundsParametersPath


class ListGuildSoundboardSoundsHTTPResponseBody(
  RootModel[
    http.ListGuildSoundboardSoundsResponse
    | http.RatelimitedResponse
    | http.ErrorResponse
  ]
):
  pass


class ListGuildSoundboardSoundsHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: ListGuildSoundboardSoundsHTTPResponseBody | None = None
  raw_body: bytes


class CreateGuildSoundboardSoundHTTPRequest(DiscordModel):
  path: http.CreateGuildSoundboardSoundParametersPath
  body: http.SoundboardCreateRequest
  content_type: str = 'application/json'


class CreateGuildSoundboardSoundHTTPResponseBody(
  RootModel[
    http.SoundboardSoundResponse | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class CreateGuildSoundboardSoundHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: CreateGuildSoundboardSoundHTTPResponseBody | None = None
  raw_body: bytes


class DeleteGuildSoundboardSoundHTTPRequest(DiscordModel):
  path: http.DeleteGuildSoundboardSoundParametersPath


class DeleteGuildSoundboardSoundHTTPResponseBody(
  RootModel[http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class DeleteGuildSoundboardSoundHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: DeleteGuildSoundboardSoundHTTPResponseBody | None = None
  raw_body: bytes


class GetGuildSoundboardSoundHTTPRequest(DiscordModel):
  path: http.GetGuildSoundboardSoundParametersPath


class GetGuildSoundboardSoundHTTPResponseBody(
  RootModel[
    http.SoundboardSoundResponse | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class GetGuildSoundboardSoundHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetGuildSoundboardSoundHTTPResponseBody | None = None
  raw_body: bytes


class UpdateGuildSoundboardSoundHTTPRequest(DiscordModel):
  path: http.UpdateGuildSoundboardSoundParametersPath
  body: http.SoundboardPatchRequestPartial
  content_type: str = 'application/json'


class UpdateGuildSoundboardSoundHTTPResponseBody(
  RootModel[
    http.SoundboardSoundResponse | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class UpdateGuildSoundboardSoundHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: UpdateGuildSoundboardSoundHTTPResponseBody | None = None
  raw_body: bytes


class ListGuildStickersHTTPRequest(DiscordModel):
  path: http.ListGuildStickersParametersPath


class ListGuildStickersHTTPResponseBody(
  RootModel[
    http.ListGuildStickersResponse200 | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class ListGuildStickersHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: ListGuildStickersHTTPResponseBody | None = None
  raw_body: bytes


class CreateGuildStickerHTTPRequest(DiscordModel):
  path: http.CreateGuildStickerParametersPath
  body: http.CreateGuildStickerRequest
  content_type: str = 'multipart/form-data'


class CreateGuildStickerHTTPResponseBody(
  RootModel[http.GuildStickerResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class CreateGuildStickerHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: CreateGuildStickerHTTPResponseBody | None = None
  raw_body: bytes


class DeleteGuildStickerHTTPRequest(DiscordModel):
  path: http.DeleteGuildStickerParametersPath


class DeleteGuildStickerHTTPResponseBody(
  RootModel[http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class DeleteGuildStickerHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: DeleteGuildStickerHTTPResponseBody | None = None
  raw_body: bytes


class GetGuildStickerHTTPRequest(DiscordModel):
  path: http.GetGuildStickerParametersPath


class GetGuildStickerHTTPResponseBody(
  RootModel[http.GuildStickerResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class GetGuildStickerHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetGuildStickerHTTPResponseBody | None = None
  raw_body: bytes


class UpdateGuildStickerHTTPRequest(DiscordModel):
  path: http.UpdateGuildStickerParametersPath
  body: http.UpdateGuildStickerRequest
  content_type: str = 'application/json'


class UpdateGuildStickerHTTPResponseBody(
  RootModel[http.GuildStickerResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class UpdateGuildStickerHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: UpdateGuildStickerHTTPResponseBody | None = None
  raw_body: bytes


class ListGuildTemplatesHTTPRequest(DiscordModel):
  path: http.ListGuildTemplatesParametersPath


class ListGuildTemplatesHTTPResponseBody(
  RootModel[
    http.ListGuildTemplatesResponse200 | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class ListGuildTemplatesHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: ListGuildTemplatesHTTPResponseBody | None = None
  raw_body: bytes


class CreateGuildTemplateHTTPRequest(DiscordModel):
  path: http.CreateGuildTemplateParametersPath
  body: http.CreateGuildTemplateRequest
  content_type: str = 'application/json'


class CreateGuildTemplateHTTPResponseBody(
  RootModel[http.GuildTemplateResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class CreateGuildTemplateHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: CreateGuildTemplateHTTPResponseBody | None = None
  raw_body: bytes


class DeleteGuildTemplateHTTPRequest(DiscordModel):
  path: http.DeleteGuildTemplateParametersPath


class DeleteGuildTemplateHTTPResponseBody(
  RootModel[http.GuildTemplateResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class DeleteGuildTemplateHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: DeleteGuildTemplateHTTPResponseBody | None = None
  raw_body: bytes


class UpdateGuildTemplateHTTPRequest(DiscordModel):
  path: http.UpdateGuildTemplateParametersPath
  body: http.UpdateGuildTemplateRequest
  content_type: str = 'application/json'


class UpdateGuildTemplateHTTPResponseBody(
  RootModel[http.GuildTemplateResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class UpdateGuildTemplateHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: UpdateGuildTemplateHTTPResponseBody | None = None
  raw_body: bytes


class SyncGuildTemplateHTTPRequest(DiscordModel):
  path: http.SyncGuildTemplateParametersPath


class SyncGuildTemplateHTTPResponseBody(
  RootModel[http.GuildTemplateResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class SyncGuildTemplateHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: SyncGuildTemplateHTTPResponseBody | None = None
  raw_body: bytes


class GetActiveGuildThreadsHTTPRequest(DiscordModel):
  path: http.GetActiveGuildThreadsParametersPath


class GetActiveGuildThreadsHTTPResponseBody(
  RootModel[http.ThreadsResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class GetActiveGuildThreadsHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetActiveGuildThreadsHTTPResponseBody | None = None
  raw_body: bytes


class GetGuildVanityUrlHTTPRequest(DiscordModel):
  path: http.GetGuildVanityUrlParametersPath


class GetGuildVanityUrlHTTPResponseBody(
  RootModel[http.VanityURLResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class GetGuildVanityUrlHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetGuildVanityUrlHTTPResponseBody | None = None
  raw_body: bytes


class GetSelfVoiceStateHTTPRequest(DiscordModel):
  path: http.GetSelfVoiceStateParametersPath


class GetSelfVoiceStateHTTPResponseBody(
  RootModel[http.VoiceStateResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class GetSelfVoiceStateHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetSelfVoiceStateHTTPResponseBody | None = None
  raw_body: bytes


class UpdateSelfVoiceStateHTTPRequest(DiscordModel):
  path: http.UpdateSelfVoiceStateParametersPath
  body: http.UpdateSelfVoiceStateRequestPartial
  content_type: str = 'application/json'


class UpdateSelfVoiceStateHTTPResponseBody(
  RootModel[http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class UpdateSelfVoiceStateHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: UpdateSelfVoiceStateHTTPResponseBody | None = None
  raw_body: bytes


class GetVoiceStateHTTPRequest(DiscordModel):
  path: http.GetVoiceStateParametersPath


class GetVoiceStateHTTPResponseBody(
  RootModel[http.VoiceStateResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class GetVoiceStateHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetVoiceStateHTTPResponseBody | None = None
  raw_body: bytes


class UpdateVoiceStateHTTPRequest(DiscordModel):
  path: http.UpdateVoiceStateParametersPath
  body: http.UpdateVoiceStateRequestPartial
  content_type: str = 'application/json'


class UpdateVoiceStateHTTPResponseBody(
  RootModel[http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class UpdateVoiceStateHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: UpdateVoiceStateHTTPResponseBody | None = None
  raw_body: bytes


class GetGuildWebhooksHTTPRequest(DiscordModel):
  path: http.GetGuildWebhooksParametersPath


class GetGuildWebhooksHTTPResponseBody(
  RootModel[
    http.GetGuildWebhooksResponse200 | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class GetGuildWebhooksHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetGuildWebhooksHTTPResponseBody | None = None
  raw_body: bytes


class GetGuildWelcomeScreenHTTPRequest(DiscordModel):
  path: http.GetGuildWelcomeScreenParametersPath


class GetGuildWelcomeScreenHTTPResponseBody(
  RootModel[
    http.GuildWelcomeScreenResponse | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class GetGuildWelcomeScreenHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetGuildWelcomeScreenHTTPResponseBody | None = None
  raw_body: bytes


class UpdateGuildWelcomeScreenHTTPRequest(DiscordModel):
  path: http.UpdateGuildWelcomeScreenParametersPath
  body: http.WelcomeScreenPatchRequestPartial
  content_type: str = 'application/json'


class UpdateGuildWelcomeScreenHTTPResponseBody(
  RootModel[
    http.GuildWelcomeScreenResponse | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class UpdateGuildWelcomeScreenHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: UpdateGuildWelcomeScreenHTTPResponseBody | None = None
  raw_body: bytes


class GetGuildWidgetSettingsHTTPRequest(DiscordModel):
  path: http.GetGuildWidgetSettingsParametersPath


class GetGuildWidgetSettingsHTTPResponseBody(
  RootModel[http.WidgetSettingsResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class GetGuildWidgetSettingsHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetGuildWidgetSettingsHTTPResponseBody | None = None
  raw_body: bytes


class UpdateGuildWidgetSettingsHTTPRequest(DiscordModel):
  path: http.UpdateGuildWidgetSettingsParametersPath
  body: http.UpdateGuildWidgetSettingsRequest
  content_type: str = 'application/json'


class UpdateGuildWidgetSettingsHTTPResponseBody(
  RootModel[http.WidgetSettingsResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class UpdateGuildWidgetSettingsHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: UpdateGuildWidgetSettingsHTTPResponseBody | None = None
  raw_body: bytes


class GetGuildWidgetHTTPRequest(DiscordModel):
  path: http.GetGuildWidgetParametersPath


class GetGuildWidgetHTTPResponseBody(
  RootModel[http.WidgetResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class GetGuildWidgetHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetGuildWidgetHTTPResponseBody | None = None
  raw_body: bytes


class GetGuildWidgetPngHTTPRequest(DiscordModel):
  path: http.GetGuildWidgetPngParametersPath
  query: http.GetGuildWidgetPngParametersQuery | None = None


class GetGuildWidgetPngHTTPResponseBody(
  RootModel[http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class GetGuildWidgetPngHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetGuildWidgetPngHTTPResponseBody | None = None
  raw_body: bytes


class CreateInteractionResponseHTTPRequest(DiscordModel):
  path: http.CreateInteractionResponseParametersPath
  query: http.CreateInteractionResponseParametersQuery | None = None
  body: http.CreateInteractionResponseRequest
  content_type: str = 'application/json'


class CreateInteractionResponseHTTPResponseBody(
  RootModel[
    http.InteractionCallbackResponse | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class CreateInteractionResponseHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: CreateInteractionResponseHTTPResponseBody | None = None
  raw_body: bytes


class InviteRevokeHTTPRequest(DiscordModel):
  path: http.InviteRevokeParametersPath


class InviteRevokeHTTPResponseBody(
  RootModel[
    http.InviteRevokeResponse200 | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class InviteRevokeHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: InviteRevokeHTTPResponseBody | None = None
  raw_body: bytes


class InviteResolveHTTPRequest(DiscordModel):
  path: http.InviteResolveParametersPath
  query: http.InviteResolveParametersQuery | None = None


class InviteResolveHTTPResponseBody(
  RootModel[
    http.InviteResolveResponse200 | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class InviteResolveHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: InviteResolveHTTPResponseBody | None = None
  raw_body: bytes


class GetInviteTargetUsersHTTPRequest(DiscordModel):
  path: http.GetInviteTargetUsersParametersPath


class GetInviteTargetUsersHTTPResponseBody(
  RootModel[http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class GetInviteTargetUsersHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetInviteTargetUsersHTTPResponseBody | None = None
  raw_body: bytes


class UpdateInviteTargetUsersHTTPRequest(DiscordModel):
  path: http.UpdateInviteTargetUsersParametersPath
  body: http.UpdateInviteTargetUsersRequest
  content_type: str = 'multipart/form-data'


class UpdateInviteTargetUsersHTTPResponseBody(
  RootModel[http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class UpdateInviteTargetUsersHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: UpdateInviteTargetUsersHTTPResponseBody | None = None
  raw_body: bytes


class GetInviteTargetUsersJobStatusHTTPRequest(DiscordModel):
  path: http.GetInviteTargetUsersJobStatusParametersPath


class GetInviteTargetUsersJobStatusHTTPResponseBody(
  RootModel[
    http.TargetUsersJobStatusResponse | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class GetInviteTargetUsersJobStatusHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetInviteTargetUsersJobStatusHTTPResponseBody | None = None
  raw_body: bytes


class CreateLobbyHTTPRequest(DiscordModel):
  body: http.CreateLobbyRequest
  content_type: str = 'application/json'


class CreateLobbyHTTPResponseBody(
  RootModel[http.LobbyResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class CreateLobbyHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: CreateLobbyHTTPResponseBody | None = None
  raw_body: bytes


class CreateOrJoinLobbyHTTPRequest(DiscordModel):
  body: http.CreateOrJoinLobbyRequest
  content_type: str = 'application/json'


class CreateOrJoinLobbyHTTPResponseBody(
  RootModel[http.LobbyResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class CreateOrJoinLobbyHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: CreateOrJoinLobbyHTTPResponseBody | None = None
  raw_body: bytes


class DeleteLobbyHTTPRequest(DiscordModel):
  path: http.DeleteLobbyParametersPath


class DeleteLobbyHTTPResponseBody(
  RootModel[http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class DeleteLobbyHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: DeleteLobbyHTTPResponseBody | None = None
  raw_body: bytes


class GetLobbyHTTPRequest(DiscordModel):
  path: http.GetLobbyParametersPath


class GetLobbyHTTPResponseBody(
  RootModel[http.LobbyResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class GetLobbyHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetLobbyHTTPResponseBody | None = None
  raw_body: bytes


class EditLobbyHTTPRequest(DiscordModel):
  path: http.EditLobbyParametersPath
  body: http.EditLobbyRequest
  content_type: str = 'application/json'


class EditLobbyHTTPResponseBody(
  RootModel[http.LobbyResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class EditLobbyHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: EditLobbyHTTPResponseBody | None = None
  raw_body: bytes


class EditLobbyChannelLinkHTTPRequest(DiscordModel):
  path: http.EditLobbyChannelLinkParametersPath
  body: http.EditLobbyChannelLinkRequest
  content_type: str = 'application/json'


class EditLobbyChannelLinkHTTPResponseBody(
  RootModel[http.LobbyResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class EditLobbyChannelLinkHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: EditLobbyChannelLinkHTTPResponseBody | None = None
  raw_body: bytes


class LeaveLobbyHTTPRequest(DiscordModel):
  path: http.LeaveLobbyParametersPath


class LeaveLobbyHTTPResponseBody(
  RootModel[http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class LeaveLobbyHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: LeaveLobbyHTTPResponseBody | None = None
  raw_body: bytes


class CreateLinkedLobbyGuildInviteForSelfHTTPRequest(DiscordModel):
  path: http.CreateLinkedLobbyGuildInviteForSelfParametersPath


class CreateLinkedLobbyGuildInviteForSelfHTTPResponseBody(
  RootModel[
    http.LobbyGuildInviteResponse | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class CreateLinkedLobbyGuildInviteForSelfHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: CreateLinkedLobbyGuildInviteForSelfHTTPResponseBody | None = None
  raw_body: bytes


class BulkUpdateLobbyMembersHTTPRequest(DiscordModel):
  path: http.BulkUpdateLobbyMembersParametersPath
  body: http.BulkUpdateLobbyMembersRequest
  content_type: str = 'application/json'


class BulkUpdateLobbyMembersHTTPResponseBody(
  RootModel[
    http.BulkUpdateLobbyMembersResponse200
    | http.RatelimitedResponse
    | http.ErrorResponse
  ]
):
  pass


class BulkUpdateLobbyMembersHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: BulkUpdateLobbyMembersHTTPResponseBody | None = None
  raw_body: bytes


class DeleteLobbyMemberHTTPRequest(DiscordModel):
  path: http.DeleteLobbyMemberParametersPath


class DeleteLobbyMemberHTTPResponseBody(
  RootModel[http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class DeleteLobbyMemberHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: DeleteLobbyMemberHTTPResponseBody | None = None
  raw_body: bytes


class AddLobbyMemberHTTPRequest(DiscordModel):
  path: http.AddLobbyMemberParametersPath
  body: http.AddLobbyMemberRequest
  content_type: str = 'application/json'


class AddLobbyMemberHTTPResponseBody(
  RootModel[http.LobbyMemberResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class AddLobbyMemberHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: AddLobbyMemberHTTPResponseBody | None = None
  raw_body: bytes


class CreateLinkedLobbyGuildInviteForUserHTTPRequest(DiscordModel):
  path: http.CreateLinkedLobbyGuildInviteForUserParametersPath


class CreateLinkedLobbyGuildInviteForUserHTTPResponseBody(
  RootModel[
    http.LobbyGuildInviteResponse | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class CreateLinkedLobbyGuildInviteForUserHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: CreateLinkedLobbyGuildInviteForUserHTTPResponseBody | None = None
  raw_body: bytes


class GetLobbyMessagesHTTPRequest(DiscordModel):
  path: http.GetLobbyMessagesParametersPath
  query: http.GetLobbyMessagesParametersQuery | None = None


class GetLobbyMessagesHTTPResponseBody(
  RootModel[
    http.GetLobbyMessagesResponse200 | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class GetLobbyMessagesHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetLobbyMessagesHTTPResponseBody | None = None
  raw_body: bytes


class CreateLobbyMessageHTTPRequest(DiscordModel):
  path: http.CreateLobbyMessageParametersPath
  body: http.SDKMessageRequest
  content_type: str = 'application/json'


class CreateLobbyMessageHTTPResponseBody(
  RootModel[http.LobbyMessageResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class CreateLobbyMessageHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: CreateLobbyMessageHTTPResponseBody | None = None
  raw_body: bytes


class UpdateLobbyMessageExternalModerationMetadataHTTPRequest(DiscordModel):
  path: http.UpdateLobbyMessageExternalModerationMetadataParametersPath
  body: http.UpdateLobbyMessageExternalModerationMetadataRequest
  content_type: str = 'application/json'


class UpdateLobbyMessageExternalModerationMetadataHTTPResponseBody(
  RootModel[http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class UpdateLobbyMessageExternalModerationMetadataHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: UpdateLobbyMessageExternalModerationMetadataHTTPResponseBody | None = None
  raw_body: bytes


class GetMyOauth2AuthorizationHTTPRequest(DiscordModel):
  pass


class GetMyOauth2AuthorizationHTTPResponseBody(
  RootModel[
    http.OAuth2GetAuthorizationResponse | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class GetMyOauth2AuthorizationHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetMyOauth2AuthorizationHTTPResponseBody | None = None
  raw_body: bytes


class GetMyOauth2ApplicationHTTPRequest(DiscordModel):
  pass


class GetMyOauth2ApplicationHTTPResponseBody(
  RootModel[
    http.PrivateApplicationResponse | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class GetMyOauth2ApplicationHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetMyOauth2ApplicationHTTPResponseBody | None = None
  raw_body: bytes


class GetPublicKeysHTTPRequest(DiscordModel):
  pass


class GetPublicKeysHTTPResponseBody(
  RootModel[http.OAuth2GetKeys | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class GetPublicKeysHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetPublicKeysHTTPResponseBody | None = None
  raw_body: bytes


class GetOpenidConnectUserinfoHTTPRequest(DiscordModel):
  pass


class GetOpenidConnectUserinfoHTTPResponseBody(
  RootModel[
    http.OAuth2GetOpenIDConnectUserInfoResponse
    | http.RatelimitedResponse
    | http.ErrorResponse
  ]
):
  pass


class GetOpenidConnectUserinfoHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetOpenidConnectUserinfoHTTPResponseBody | None = None
  raw_body: bytes


class UpdateUserMessageExternalModerationMetadataHTTPRequest(DiscordModel):
  path: http.UpdateUserMessageExternalModerationMetadataParametersPath
  body: http.UpdateUserMessageExternalModerationMetadataRequest
  content_type: str = 'application/json'


class UpdateUserMessageExternalModerationMetadataHTTPResponseBody(
  RootModel[http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class UpdateUserMessageExternalModerationMetadataHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: UpdateUserMessageExternalModerationMetadataHTTPResponseBody | None = None
  raw_body: bytes


class PartnerSdkUnmergeProvisionalAccountHTTPRequest(DiscordModel):
  body: http.PartnerSdkUnmergeProvisionalAccountRequest
  content_type: str = 'application/json'


class PartnerSdkUnmergeProvisionalAccountHTTPResponseBody(
  RootModel[http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class PartnerSdkUnmergeProvisionalAccountHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: PartnerSdkUnmergeProvisionalAccountHTTPResponseBody | None = None
  raw_body: bytes


class BotPartnerSdkUnmergeProvisionalAccountHTTPRequest(DiscordModel):
  body: http.BotPartnerSdkUnmergeProvisionalAccountRequest
  content_type: str = 'application/json'


class BotPartnerSdkUnmergeProvisionalAccountHTTPResponseBody(
  RootModel[http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class BotPartnerSdkUnmergeProvisionalAccountHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: BotPartnerSdkUnmergeProvisionalAccountHTTPResponseBody | None = None
  raw_body: bytes


class PartnerSdkTokenHTTPRequest(DiscordModel):
  body: http.PartnerSdkTokenRequest
  content_type: str = 'application/json'


class PartnerSdkTokenHTTPResponseBody(
  RootModel[
    http.ProvisionalTokenResponse | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class PartnerSdkTokenHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: PartnerSdkTokenHTTPResponseBody | None = None
  raw_body: bytes


class BotPartnerSdkTokenHTTPRequest(DiscordModel):
  body: http.BotPartnerSdkTokenRequest
  content_type: str = 'application/json'


class BotPartnerSdkTokenHTTPResponseBody(
  RootModel[
    http.ProvisionalTokenResponse | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class BotPartnerSdkTokenHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: BotPartnerSdkTokenHTTPResponseBody | None = None
  raw_body: bytes


class GetSkuSubscriptionsHTTPRequest(DiscordModel):
  path: http.GetSkuSubscriptionsParametersPath
  query: http.GetSkuSubscriptionsParametersQuery | None = None


class GetSkuSubscriptionsHTTPResponseBody(
  RootModel[
    http.GetSkuSubscriptionsResponse200 | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class GetSkuSubscriptionsHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetSkuSubscriptionsHTTPResponseBody | None = None
  raw_body: bytes


class GetSkuSubscriptionHTTPRequest(DiscordModel):
  path: http.GetSkuSubscriptionParametersPath
  query: http.GetSkuSubscriptionParametersQuery | None = None


class GetSkuSubscriptionHTTPResponseBody(
  RootModel[http.SubscriptionResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class GetSkuSubscriptionHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetSkuSubscriptionHTTPResponseBody | None = None
  raw_body: bytes


class GetSoundboardDefaultSoundsHTTPRequest(DiscordModel):
  pass


class GetSoundboardDefaultSoundsHTTPResponseBody(
  RootModel[
    http.GetSoundboardDefaultSoundsResponse200
    | http.RatelimitedResponse
    | http.ErrorResponse
  ]
):
  pass


class GetSoundboardDefaultSoundsHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetSoundboardDefaultSoundsHTTPResponseBody | None = None
  raw_body: bytes


class CreateStageInstanceHTTPRequest(DiscordModel):
  body: http.CreateStageInstanceRequest
  content_type: str = 'application/json'


class CreateStageInstanceHTTPResponseBody(
  RootModel[http.StageInstanceResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class CreateStageInstanceHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: CreateStageInstanceHTTPResponseBody | None = None
  raw_body: bytes


class DeleteStageInstanceHTTPRequest(DiscordModel):
  path: http.DeleteStageInstanceParametersPath


class DeleteStageInstanceHTTPResponseBody(
  RootModel[http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class DeleteStageInstanceHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: DeleteStageInstanceHTTPResponseBody | None = None
  raw_body: bytes


class GetStageInstanceHTTPRequest(DiscordModel):
  path: http.GetStageInstanceParametersPath


class GetStageInstanceHTTPResponseBody(
  RootModel[http.StageInstanceResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class GetStageInstanceHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetStageInstanceHTTPResponseBody | None = None
  raw_body: bytes


class UpdateStageInstanceHTTPRequest(DiscordModel):
  path: http.UpdateStageInstanceParametersPath
  body: http.UpdateStageInstanceRequest
  content_type: str = 'application/json'


class UpdateStageInstanceHTTPResponseBody(
  RootModel[http.StageInstanceResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class UpdateStageInstanceHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: UpdateStageInstanceHTTPResponseBody | None = None
  raw_body: bytes


class ListStickerPacksHTTPRequest(DiscordModel):
  pass


class ListStickerPacksHTTPResponseBody(
  RootModel[
    http.StickerPackCollectionResponse | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class ListStickerPacksHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: ListStickerPacksHTTPResponseBody | None = None
  raw_body: bytes


class GetStickerPackHTTPRequest(DiscordModel):
  path: http.GetStickerPackParametersPath


class GetStickerPackHTTPResponseBody(
  RootModel[http.StickerPackResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class GetStickerPackHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetStickerPackHTTPResponseBody | None = None
  raw_body: bytes


class GetStickerHTTPRequest(DiscordModel):
  path: http.GetStickerParametersPath


class GetStickerHTTPResponseBody(
  RootModel[http.GetStickerResponse200 | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class GetStickerHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetStickerHTTPResponseBody | None = None
  raw_body: bytes


class GetMyUserHTTPRequest(DiscordModel):
  pass


class GetMyUserHTTPResponseBody(
  RootModel[http.UserPIIResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class GetMyUserHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetMyUserHTTPResponseBody | None = None
  raw_body: bytes


class UpdateMyUserHTTPRequest(DiscordModel):
  body: http.BotAccountPatchRequest
  content_type: str = 'application/json'


class UpdateMyUserHTTPResponseBody(
  RootModel[http.UserPIIResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class UpdateMyUserHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: UpdateMyUserHTTPResponseBody | None = None
  raw_body: bytes


class GetCurrentUserApplicationEntitlementsHTTPRequest(DiscordModel):
  path: http.GetCurrentUserApplicationEntitlementsParametersPath
  query: http.GetCurrentUserApplicationEntitlementsParametersQuery | None = None


class GetCurrentUserApplicationEntitlementsHTTPResponseBody(
  RootModel[
    http.GetCurrentUserApplicationEntitlementsResponse200
    | http.RatelimitedResponse
    | http.ErrorResponse
  ]
):
  pass


class GetCurrentUserApplicationEntitlementsHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetCurrentUserApplicationEntitlementsHTTPResponseBody | None = None
  raw_body: bytes


class DeleteApplicationUserRoleConnectionHTTPRequest(DiscordModel):
  path: http.DeleteApplicationUserRoleConnectionParametersPath


class DeleteApplicationUserRoleConnectionHTTPResponseBody(
  RootModel[http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class DeleteApplicationUserRoleConnectionHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: DeleteApplicationUserRoleConnectionHTTPResponseBody | None = None
  raw_body: bytes


class GetApplicationUserRoleConnectionHTTPRequest(DiscordModel):
  path: http.GetApplicationUserRoleConnectionParametersPath


class GetApplicationUserRoleConnectionHTTPResponseBody(
  RootModel[
    http.ApplicationUserRoleConnectionResponse
    | http.RatelimitedResponse
    | http.ErrorResponse
  ]
):
  pass


class GetApplicationUserRoleConnectionHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetApplicationUserRoleConnectionHTTPResponseBody | None = None
  raw_body: bytes


class UpdateApplicationUserRoleConnectionHTTPRequest(DiscordModel):
  path: http.UpdateApplicationUserRoleConnectionParametersPath
  body: http.UpdateApplicationUserRoleConnectionRequest
  content_type: str = 'application/json'


class UpdateApplicationUserRoleConnectionHTTPResponseBody(
  RootModel[
    http.ApplicationUserRoleConnectionResponse
    | http.RatelimitedResponse
    | http.ErrorResponse
  ]
):
  pass


class UpdateApplicationUserRoleConnectionHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: UpdateApplicationUserRoleConnectionHTTPResponseBody | None = None
  raw_body: bytes


class CreateDmHTTPRequest(DiscordModel):
  body: http.CreatePrivateChannelRequest
  content_type: str = 'application/json'


class CreateDmHTTPResponseBody(
  RootModel[http.CreateDmResponse200 | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class CreateDmHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: CreateDmHTTPResponseBody | None = None
  raw_body: bytes


class ListMyConnectionsHTTPRequest(DiscordModel):
  pass


class ListMyConnectionsHTTPResponseBody(
  RootModel[
    http.ListMyConnectionsResponse200 | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class ListMyConnectionsHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: ListMyConnectionsHTTPResponseBody | None = None
  raw_body: bytes


class ListMyGuildsHTTPRequest(DiscordModel):
  query: http.ListMyGuildsParametersQuery | None = None


class ListMyGuildsHTTPResponseBody(
  RootModel[
    http.ListMyGuildsResponse200 | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class ListMyGuildsHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: ListMyGuildsHTTPResponseBody | None = None
  raw_body: bytes


class LeaveGuildHTTPRequest(DiscordModel):
  path: http.LeaveGuildParametersPath


class LeaveGuildHTTPResponseBody(
  RootModel[http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class LeaveGuildHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: LeaveGuildHTTPResponseBody | None = None
  raw_body: bytes


class GetMyGuildMemberHTTPRequest(DiscordModel):
  path: http.GetMyGuildMemberParametersPath


class GetMyGuildMemberHTTPResponseBody(
  RootModel[
    http.PrivateGuildMemberResponse | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class GetMyGuildMemberHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetMyGuildMemberHTTPResponseBody | None = None
  raw_body: bytes


class GetUserHTTPRequest(DiscordModel):
  path: http.GetUserParametersPath


class GetUserHTTPResponseBody(
  RootModel[http.UserResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class GetUserHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetUserHTTPResponseBody | None = None
  raw_body: bytes


class ListVoiceRegionsHTTPRequest(DiscordModel):
  pass


class ListVoiceRegionsHTTPResponseBody(
  RootModel[
    http.ListVoiceRegionsResponse200 | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class ListVoiceRegionsHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: ListVoiceRegionsHTTPResponseBody | None = None
  raw_body: bytes


class DeleteWebhookHTTPRequest(DiscordModel):
  path: http.DeleteWebhookParametersPath


class DeleteWebhookHTTPResponseBody(
  RootModel[http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class DeleteWebhookHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: DeleteWebhookHTTPResponseBody | None = None
  raw_body: bytes


class GetWebhookHTTPRequest(DiscordModel):
  path: http.GetWebhookParametersPath


class GetWebhookHTTPResponseBody(
  RootModel[http.GetWebhookResponse200 | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class GetWebhookHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetWebhookHTTPResponseBody | None = None
  raw_body: bytes


class UpdateWebhookHTTPRequest(DiscordModel):
  path: http.UpdateWebhookParametersPath
  body: http.UpdateWebhookRequest
  content_type: str = 'application/json'


class UpdateWebhookHTTPResponseBody(
  RootModel[
    http.UpdateWebhookResponse200 | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class UpdateWebhookHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: UpdateWebhookHTTPResponseBody | None = None
  raw_body: bytes


class DeleteWebhookByTokenHTTPRequest(DiscordModel):
  path: http.DeleteWebhookByTokenParametersPath


class DeleteWebhookByTokenHTTPResponseBody(
  RootModel[http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class DeleteWebhookByTokenHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: DeleteWebhookByTokenHTTPResponseBody | None = None
  raw_body: bytes


class GetWebhookByTokenHTTPRequest(DiscordModel):
  path: http.GetWebhookByTokenParametersPath


class GetWebhookByTokenHTTPResponseBody(
  RootModel[
    http.GetWebhookByTokenResponse200 | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class GetWebhookByTokenHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetWebhookByTokenHTTPResponseBody | None = None
  raw_body: bytes


class UpdateWebhookByTokenHTTPRequest(DiscordModel):
  path: http.UpdateWebhookByTokenParametersPath
  body: http.UpdateWebhookByTokenRequest
  content_type: str = 'application/json'


class UpdateWebhookByTokenHTTPResponseBody(
  RootModel[
    http.UpdateWebhookByTokenResponse200 | http.RatelimitedResponse | http.ErrorResponse
  ]
):
  pass


class UpdateWebhookByTokenHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: UpdateWebhookByTokenHTTPResponseBody | None = None
  raw_body: bytes


class ExecuteWebhookHTTPRequest(DiscordModel):
  path: http.ExecuteWebhookParametersPath
  query: http.ExecuteWebhookParametersQuery | None = None
  body: http.ExecuteWebhookRequest
  content_type: str = 'application/json'


class ExecuteWebhookHTTPResponseBody(
  RootModel[http.MessageResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class ExecuteWebhookHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: ExecuteWebhookHTTPResponseBody | None = None
  raw_body: bytes


class ExecuteGithubCompatibleWebhookHTTPRequest(DiscordModel):
  path: http.ExecuteGithubCompatibleWebhookParametersPath
  query: http.ExecuteGithubCompatibleWebhookParametersQuery | None = None
  body: http.GithubWebhook
  content_type: str = 'application/json'


class ExecuteGithubCompatibleWebhookHTTPResponseBody(
  RootModel[http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class ExecuteGithubCompatibleWebhookHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: ExecuteGithubCompatibleWebhookHTTPResponseBody | None = None
  raw_body: bytes


class DeleteOriginalWebhookMessageHTTPRequest(DiscordModel):
  path: http.DeleteOriginalWebhookMessageParametersPath
  query: http.DeleteOriginalWebhookMessageParametersQuery | None = None


class DeleteOriginalWebhookMessageHTTPResponseBody(
  RootModel[http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class DeleteOriginalWebhookMessageHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: DeleteOriginalWebhookMessageHTTPResponseBody | None = None
  raw_body: bytes


class GetOriginalWebhookMessageHTTPRequest(DiscordModel):
  path: http.GetOriginalWebhookMessageParametersPath
  query: http.GetOriginalWebhookMessageParametersQuery | None = None


class GetOriginalWebhookMessageHTTPResponseBody(
  RootModel[http.MessageResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class GetOriginalWebhookMessageHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetOriginalWebhookMessageHTTPResponseBody | None = None
  raw_body: bytes


class UpdateOriginalWebhookMessageHTTPRequest(DiscordModel):
  path: http.UpdateOriginalWebhookMessageParametersPath
  query: http.UpdateOriginalWebhookMessageParametersQuery | None = None
  body: http.UpdateOriginalWebhookMessageRequest
  content_type: str = 'application/json'


class UpdateOriginalWebhookMessageHTTPResponseBody(
  RootModel[http.MessageResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class UpdateOriginalWebhookMessageHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: UpdateOriginalWebhookMessageHTTPResponseBody | None = None
  raw_body: bytes


class DeleteWebhookMessageHTTPRequest(DiscordModel):
  path: http.DeleteWebhookMessageParametersPath
  query: http.DeleteWebhookMessageParametersQuery | None = None


class DeleteWebhookMessageHTTPResponseBody(
  RootModel[http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class DeleteWebhookMessageHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: DeleteWebhookMessageHTTPResponseBody | None = None
  raw_body: bytes


class GetWebhookMessageHTTPRequest(DiscordModel):
  path: http.GetWebhookMessageParametersPath
  query: http.GetWebhookMessageParametersQuery | None = None


class GetWebhookMessageHTTPResponseBody(
  RootModel[http.MessageResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class GetWebhookMessageHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetWebhookMessageHTTPResponseBody | None = None
  raw_body: bytes


class UpdateWebhookMessageHTTPRequest(DiscordModel):
  path: http.UpdateWebhookMessageParametersPath
  query: http.UpdateWebhookMessageParametersQuery | None = None
  body: http.UpdateWebhookMessageRequest
  content_type: str = 'application/json'


class UpdateWebhookMessageHTTPResponseBody(
  RootModel[http.MessageResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class UpdateWebhookMessageHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: UpdateWebhookMessageHTTPResponseBody | None = None
  raw_body: bytes


class ExecuteSlackCompatibleWebhookHTTPRequest(DiscordModel):
  path: http.ExecuteSlackCompatibleWebhookParametersPath
  query: http.ExecuteSlackCompatibleWebhookParametersQuery | None = None
  body: http.SlackWebhook
  content_type: str = 'application/json'


class ExecuteSlackCompatibleWebhookHTTPResponseBody(
  RootModel[http.RatelimitedResponse | http.ErrorResponse]
):
  pass


class ExecuteSlackCompatibleWebhookHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: ExecuteSlackCompatibleWebhookHTTPResponseBody | None = None
  raw_body: bytes


__all__ = (
  "ActionGuildJoinRequestHTTPRequest",
  "ActionGuildJoinRequestHTTPResponse",
  "ActionGuildJoinRequestHTTPResponseBody",
  "AddGroupDmUserHTTPRequest",
  "AddGroupDmUserHTTPResponse",
  "AddGroupDmUserHTTPResponseBody",
  "AddGuildMemberHTTPRequest",
  "AddGuildMemberHTTPResponse",
  "AddGuildMemberHTTPResponseBody",
  "AddGuildMemberRoleHTTPRequest",
  "AddGuildMemberRoleHTTPResponse",
  "AddGuildMemberRoleHTTPResponseBody",
  "AddLobbyMemberHTTPRequest",
  "AddLobbyMemberHTTPResponse",
  "AddLobbyMemberHTTPResponseBody",
  "AddMyMessageReactionHTTPRequest",
  "AddMyMessageReactionHTTPResponse",
  "AddMyMessageReactionHTTPResponseBody",
  "AddThreadMemberHTTPRequest",
  "AddThreadMemberHTTPResponse",
  "AddThreadMemberHTTPResponseBody",
  "ApplicationsGetActivityInstanceHTTPRequest",
  "ApplicationsGetActivityInstanceHTTPResponse",
  "ApplicationsGetActivityInstanceHTTPResponseBody",
  "BanUserFromGuildHTTPRequest",
  "BanUserFromGuildHTTPResponse",
  "BanUserFromGuildHTTPResponseBody",
  "BotPartnerSdkTokenHTTPRequest",
  "BotPartnerSdkTokenHTTPResponse",
  "BotPartnerSdkTokenHTTPResponseBody",
  "BotPartnerSdkUnmergeProvisionalAccountHTTPRequest",
  "BotPartnerSdkUnmergeProvisionalAccountHTTPResponse",
  "BotPartnerSdkUnmergeProvisionalAccountHTTPResponseBody",
  "BulkBanUsersFromGuildHTTPRequest",
  "BulkBanUsersFromGuildHTTPResponse",
  "BulkBanUsersFromGuildHTTPResponseBody",
  "BulkDeleteMessagesHTTPRequest",
  "BulkDeleteMessagesHTTPResponse",
  "BulkDeleteMessagesHTTPResponseBody",
  "BulkSetApplicationCommandsHTTPRequest",
  "BulkSetApplicationCommandsHTTPResponse",
  "BulkSetApplicationCommandsHTTPResponseBody",
  "BulkSetGuildApplicationCommandsHTTPRequest",
  "BulkSetGuildApplicationCommandsHTTPResponse",
  "BulkSetGuildApplicationCommandsHTTPResponseBody",
  "BulkUpdateGuildChannelsHTTPRequest",
  "BulkUpdateGuildChannelsHTTPResponse",
  "BulkUpdateGuildChannelsHTTPResponseBody",
  "BulkUpdateGuildRolesHTTPRequest",
  "BulkUpdateGuildRolesHTTPResponse",
  "BulkUpdateGuildRolesHTTPResponseBody",
  "BulkUpdateLobbyMembersHTTPRequest",
  "BulkUpdateLobbyMembersHTTPResponse",
  "BulkUpdateLobbyMembersHTTPResponseBody",
  "ConsumeEntitlementHTTPRequest",
  "ConsumeEntitlementHTTPResponse",
  "ConsumeEntitlementHTTPResponseBody",
  "CountGuildScheduledEventUsersHTTPRequest",
  "CountGuildScheduledEventUsersHTTPResponse",
  "CountGuildScheduledEventUsersHTTPResponseBody",
  "CreateApplicationCommandHTTPRequest",
  "CreateApplicationCommandHTTPResponse",
  "CreateApplicationCommandHTTPResponseBody",
  "CreateApplicationEmojiHTTPRequest",
  "CreateApplicationEmojiHTTPResponse",
  "CreateApplicationEmojiHTTPResponseBody",
  "CreateAutoModerationRuleHTTPRequest",
  "CreateAutoModerationRuleHTTPResponse",
  "CreateAutoModerationRuleHTTPResponseBody",
  "CreateChannelInviteHTTPRequest",
  "CreateChannelInviteHTTPResponse",
  "CreateChannelInviteHTTPResponseBody",
  "CreateDmHTTPRequest",
  "CreateDmHTTPResponse",
  "CreateDmHTTPResponseBody",
  "CreateEntitlementHTTPRequest",
  "CreateEntitlementHTTPResponse",
  "CreateEntitlementHTTPResponseBody",
  "CreateGuildApplicationCommandHTTPRequest",
  "CreateGuildApplicationCommandHTTPResponse",
  "CreateGuildApplicationCommandHTTPResponseBody",
  "CreateGuildChannelHTTPRequest",
  "CreateGuildChannelHTTPResponse",
  "CreateGuildChannelHTTPResponseBody",
  "CreateGuildEmojiHTTPRequest",
  "CreateGuildEmojiHTTPResponse",
  "CreateGuildEmojiHTTPResponseBody",
  "CreateGuildRoleHTTPRequest",
  "CreateGuildRoleHTTPResponse",
  "CreateGuildRoleHTTPResponseBody",
  "CreateGuildScheduledEventExceptionHTTPRequest",
  "CreateGuildScheduledEventExceptionHTTPResponse",
  "CreateGuildScheduledEventExceptionHTTPResponseBody",
  "CreateGuildScheduledEventHTTPRequest",
  "CreateGuildScheduledEventHTTPResponse",
  "CreateGuildScheduledEventHTTPResponseBody",
  "CreateGuildSoundboardSoundHTTPRequest",
  "CreateGuildSoundboardSoundHTTPResponse",
  "CreateGuildSoundboardSoundHTTPResponseBody",
  "CreateGuildStickerHTTPRequest",
  "CreateGuildStickerHTTPResponse",
  "CreateGuildStickerHTTPResponseBody",
  "CreateGuildTemplateHTTPRequest",
  "CreateGuildTemplateHTTPResponse",
  "CreateGuildTemplateHTTPResponseBody",
  "CreateInteractionResponseHTTPRequest",
  "CreateInteractionResponseHTTPResponse",
  "CreateInteractionResponseHTTPResponseBody",
  "CreateLinkedLobbyGuildInviteForSelfHTTPRequest",
  "CreateLinkedLobbyGuildInviteForSelfHTTPResponse",
  "CreateLinkedLobbyGuildInviteForSelfHTTPResponseBody",
  "CreateLinkedLobbyGuildInviteForUserHTTPRequest",
  "CreateLinkedLobbyGuildInviteForUserHTTPResponse",
  "CreateLinkedLobbyGuildInviteForUserHTTPResponseBody",
  "CreateLobbyHTTPRequest",
  "CreateLobbyHTTPResponse",
  "CreateLobbyHTTPResponseBody",
  "CreateLobbyMessageHTTPRequest",
  "CreateLobbyMessageHTTPResponse",
  "CreateLobbyMessageHTTPResponseBody",
  "CreateMessageHTTPRequest",
  "CreateMessageHTTPResponse",
  "CreateMessageHTTPResponseBody",
  "CreateOrJoinLobbyHTTPRequest",
  "CreateOrJoinLobbyHTTPResponse",
  "CreateOrJoinLobbyHTTPResponseBody",
  "CreatePinHTTPRequest",
  "CreatePinHTTPResponse",
  "CreatePinHTTPResponseBody",
  "CreateStageInstanceHTTPRequest",
  "CreateStageInstanceHTTPResponse",
  "CreateStageInstanceHTTPResponseBody",
  "CreateThreadFromMessageHTTPRequest",
  "CreateThreadFromMessageHTTPResponse",
  "CreateThreadFromMessageHTTPResponseBody",
  "CreateThreadHTTPRequest",
  "CreateThreadHTTPResponse",
  "CreateThreadHTTPResponseBody",
  "CreateWebhookHTTPRequest",
  "CreateWebhookHTTPResponse",
  "CreateWebhookHTTPResponseBody",
  "CrosspostMessageHTTPRequest",
  "CrosspostMessageHTTPResponse",
  "CrosspostMessageHTTPResponseBody",
  "DeleteAllMessageReactionsByEmojiHTTPRequest",
  "DeleteAllMessageReactionsByEmojiHTTPResponse",
  "DeleteAllMessageReactionsByEmojiHTTPResponseBody",
  "DeleteAllMessageReactionsHTTPRequest",
  "DeleteAllMessageReactionsHTTPResponse",
  "DeleteAllMessageReactionsHTTPResponseBody",
  "DeleteApplicationCommandHTTPRequest",
  "DeleteApplicationCommandHTTPResponse",
  "DeleteApplicationCommandHTTPResponseBody",
  "DeleteApplicationEmojiHTTPRequest",
  "DeleteApplicationEmojiHTTPResponse",
  "DeleteApplicationEmojiHTTPResponseBody",
  "DeleteApplicationUserRoleConnectionHTTPRequest",
  "DeleteApplicationUserRoleConnectionHTTPResponse",
  "DeleteApplicationUserRoleConnectionHTTPResponseBody",
  "DeleteAutoModerationRuleHTTPRequest",
  "DeleteAutoModerationRuleHTTPResponse",
  "DeleteAutoModerationRuleHTTPResponseBody",
  "DeleteChannelHTTPRequest",
  "DeleteChannelHTTPResponse",
  "DeleteChannelHTTPResponseBody",
  "DeleteChannelPermissionOverwriteHTTPRequest",
  "DeleteChannelPermissionOverwriteHTTPResponse",
  "DeleteChannelPermissionOverwriteHTTPResponseBody",
  "DeleteEntitlementHTTPRequest",
  "DeleteEntitlementHTTPResponse",
  "DeleteEntitlementHTTPResponseBody",
  "DeleteGroupDmUserHTTPRequest",
  "DeleteGroupDmUserHTTPResponse",
  "DeleteGroupDmUserHTTPResponseBody",
  "DeleteGuildApplicationCommandHTTPRequest",
  "DeleteGuildApplicationCommandHTTPResponse",
  "DeleteGuildApplicationCommandHTTPResponseBody",
  "DeleteGuildEmojiHTTPRequest",
  "DeleteGuildEmojiHTTPResponse",
  "DeleteGuildEmojiHTTPResponseBody",
  "DeleteGuildIntegrationHTTPRequest",
  "DeleteGuildIntegrationHTTPResponse",
  "DeleteGuildIntegrationHTTPResponseBody",
  "DeleteGuildMemberHTTPRequest",
  "DeleteGuildMemberHTTPResponse",
  "DeleteGuildMemberHTTPResponseBody",
  "DeleteGuildMemberRoleHTTPRequest",
  "DeleteGuildMemberRoleHTTPResponse",
  "DeleteGuildMemberRoleHTTPResponseBody",
  "DeleteGuildRoleHTTPRequest",
  "DeleteGuildRoleHTTPResponse",
  "DeleteGuildRoleHTTPResponseBody",
  "DeleteGuildScheduledEventExceptionHTTPRequest",
  "DeleteGuildScheduledEventExceptionHTTPResponse",
  "DeleteGuildScheduledEventExceptionHTTPResponseBody",
  "DeleteGuildScheduledEventHTTPRequest",
  "DeleteGuildScheduledEventHTTPResponse",
  "DeleteGuildScheduledEventHTTPResponseBody",
  "DeleteGuildSoundboardSoundHTTPRequest",
  "DeleteGuildSoundboardSoundHTTPResponse",
  "DeleteGuildSoundboardSoundHTTPResponseBody",
  "DeleteGuildStickerHTTPRequest",
  "DeleteGuildStickerHTTPResponse",
  "DeleteGuildStickerHTTPResponseBody",
  "DeleteGuildTemplateHTTPRequest",
  "DeleteGuildTemplateHTTPResponse",
  "DeleteGuildTemplateHTTPResponseBody",
  "DeleteLobbyHTTPRequest",
  "DeleteLobbyHTTPResponse",
  "DeleteLobbyHTTPResponseBody",
  "DeleteLobbyMemberHTTPRequest",
  "DeleteLobbyMemberHTTPResponse",
  "DeleteLobbyMemberHTTPResponseBody",
  "DeleteMessageHTTPRequest",
  "DeleteMessageHTTPResponse",
  "DeleteMessageHTTPResponseBody",
  "DeleteMyMessageReactionHTTPRequest",
  "DeleteMyMessageReactionHTTPResponse",
  "DeleteMyMessageReactionHTTPResponseBody",
  "DeleteOriginalWebhookMessageHTTPRequest",
  "DeleteOriginalWebhookMessageHTTPResponse",
  "DeleteOriginalWebhookMessageHTTPResponseBody",
  "DeletePinHTTPRequest",
  "DeletePinHTTPResponse",
  "DeletePinHTTPResponseBody",
  "DeleteStageInstanceHTTPRequest",
  "DeleteStageInstanceHTTPResponse",
  "DeleteStageInstanceHTTPResponseBody",
  "DeleteThreadMemberHTTPRequest",
  "DeleteThreadMemberHTTPResponse",
  "DeleteThreadMemberHTTPResponseBody",
  "DeleteUserMessageReactionHTTPRequest",
  "DeleteUserMessageReactionHTTPResponse",
  "DeleteUserMessageReactionHTTPResponseBody",
  "DeleteWebhookByTokenHTTPRequest",
  "DeleteWebhookByTokenHTTPResponse",
  "DeleteWebhookByTokenHTTPResponseBody",
  "DeleteWebhookHTTPRequest",
  "DeleteWebhookHTTPResponse",
  "DeleteWebhookHTTPResponseBody",
  "DeleteWebhookMessageHTTPRequest",
  "DeleteWebhookMessageHTTPResponse",
  "DeleteWebhookMessageHTTPResponseBody",
  "DeprecatedCreatePinHTTPRequest",
  "DeprecatedCreatePinHTTPResponse",
  "DeprecatedCreatePinHTTPResponseBody",
  "DeprecatedDeletePinHTTPRequest",
  "DeprecatedDeletePinHTTPResponse",
  "DeprecatedDeletePinHTTPResponseBody",
  "DeprecatedListPinsHTTPRequest",
  "DeprecatedListPinsHTTPResponse",
  "DeprecatedListPinsHTTPResponseBody",
  "EditLobbyChannelLinkHTTPRequest",
  "EditLobbyChannelLinkHTTPResponse",
  "EditLobbyChannelLinkHTTPResponseBody",
  "EditLobbyHTTPRequest",
  "EditLobbyHTTPResponse",
  "EditLobbyHTTPResponseBody",
  "ExecuteGithubCompatibleWebhookHTTPRequest",
  "ExecuteGithubCompatibleWebhookHTTPResponse",
  "ExecuteGithubCompatibleWebhookHTTPResponseBody",
  "ExecuteSlackCompatibleWebhookHTTPRequest",
  "ExecuteSlackCompatibleWebhookHTTPResponse",
  "ExecuteSlackCompatibleWebhookHTTPResponseBody",
  "ExecuteWebhookHTTPRequest",
  "ExecuteWebhookHTTPResponse",
  "ExecuteWebhookHTTPResponseBody",
  "FollowChannelHTTPRequest",
  "FollowChannelHTTPResponse",
  "FollowChannelHTTPResponseBody",
  "GetActiveGuildThreadsHTTPRequest",
  "GetActiveGuildThreadsHTTPResponse",
  "GetActiveGuildThreadsHTTPResponseBody",
  "GetAnswerVotersHTTPRequest",
  "GetAnswerVotersHTTPResponse",
  "GetAnswerVotersHTTPResponseBody",
  "GetApplicationCommandHTTPRequest",
  "GetApplicationCommandHTTPResponse",
  "GetApplicationCommandHTTPResponseBody",
  "GetApplicationEmojiHTTPRequest",
  "GetApplicationEmojiHTTPResponse",
  "GetApplicationEmojiHTTPResponseBody",
  "GetApplicationHTTPRequest",
  "GetApplicationHTTPResponse",
  "GetApplicationHTTPResponseBody",
  "GetApplicationRoleConnectionsMetadataHTTPRequest",
  "GetApplicationRoleConnectionsMetadataHTTPResponse",
  "GetApplicationRoleConnectionsMetadataHTTPResponseBody",
  "GetApplicationUserRoleConnectionHTTPRequest",
  "GetApplicationUserRoleConnectionHTTPResponse",
  "GetApplicationUserRoleConnectionHTTPResponseBody",
  "GetAutoModerationRuleHTTPRequest",
  "GetAutoModerationRuleHTTPResponse",
  "GetAutoModerationRuleHTTPResponseBody",
  "GetBotGatewayHTTPRequest",
  "GetBotGatewayHTTPResponse",
  "GetBotGatewayHTTPResponseBody",
  "GetChannelHTTPRequest",
  "GetChannelHTTPResponse",
  "GetChannelHTTPResponseBody",
  "GetCurrentUserApplicationEntitlementsHTTPRequest",
  "GetCurrentUserApplicationEntitlementsHTTPResponse",
  "GetCurrentUserApplicationEntitlementsHTTPResponseBody",
  "GetEntitlementHTTPRequest",
  "GetEntitlementHTTPResponse",
  "GetEntitlementHTTPResponseBody",
  "GetEntitlementsHTTPRequest",
  "GetEntitlementsHTTPResponse",
  "GetEntitlementsHTTPResponseBody",
  "GetGatewayHTTPRequest",
  "GetGatewayHTTPResponse",
  "GetGatewayHTTPResponseBody",
  "GetGuildApplicationCommandHTTPRequest",
  "GetGuildApplicationCommandHTTPResponse",
  "GetGuildApplicationCommandHTTPResponseBody",
  "GetGuildApplicationCommandPermissionsHTTPRequest",
  "GetGuildApplicationCommandPermissionsHTTPResponse",
  "GetGuildApplicationCommandPermissionsHTTPResponseBody",
  "GetGuildBanHTTPRequest",
  "GetGuildBanHTTPResponse",
  "GetGuildBanHTTPResponseBody",
  "GetGuildEmojiHTTPRequest",
  "GetGuildEmojiHTTPResponse",
  "GetGuildEmojiHTTPResponseBody",
  "GetGuildHTTPRequest",
  "GetGuildHTTPResponse",
  "GetGuildHTTPResponseBody",
  "GetGuildJoinRequestsHTTPRequest",
  "GetGuildJoinRequestsHTTPResponse",
  "GetGuildJoinRequestsHTTPResponseBody",
  "GetGuildMemberHTTPRequest",
  "GetGuildMemberHTTPResponse",
  "GetGuildMemberHTTPResponseBody",
  "GetGuildNewMemberWelcomeHTTPRequest",
  "GetGuildNewMemberWelcomeHTTPResponse",
  "GetGuildNewMemberWelcomeHTTPResponseBody",
  "GetGuildPreviewHTTPRequest",
  "GetGuildPreviewHTTPResponse",
  "GetGuildPreviewHTTPResponseBody",
  "GetGuildRoleHTTPRequest",
  "GetGuildRoleHTTPResponse",
  "GetGuildRoleHTTPResponseBody",
  "GetGuildScheduledEventHTTPRequest",
  "GetGuildScheduledEventHTTPResponse",
  "GetGuildScheduledEventHTTPResponseBody",
  "GetGuildSoundboardSoundHTTPRequest",
  "GetGuildSoundboardSoundHTTPResponse",
  "GetGuildSoundboardSoundHTTPResponseBody",
  "GetGuildStickerHTTPRequest",
  "GetGuildStickerHTTPResponse",
  "GetGuildStickerHTTPResponseBody",
  "GetGuildTemplateHTTPRequest",
  "GetGuildTemplateHTTPResponse",
  "GetGuildTemplateHTTPResponseBody",
  "GetGuildVanityUrlHTTPRequest",
  "GetGuildVanityUrlHTTPResponse",
  "GetGuildVanityUrlHTTPResponseBody",
  "GetGuildWebhooksHTTPRequest",
  "GetGuildWebhooksHTTPResponse",
  "GetGuildWebhooksHTTPResponseBody",
  "GetGuildWelcomeScreenHTTPRequest",
  "GetGuildWelcomeScreenHTTPResponse",
  "GetGuildWelcomeScreenHTTPResponseBody",
  "GetGuildWidgetHTTPRequest",
  "GetGuildWidgetHTTPResponse",
  "GetGuildWidgetHTTPResponseBody",
  "GetGuildWidgetPngHTTPRequest",
  "GetGuildWidgetPngHTTPResponse",
  "GetGuildWidgetPngHTTPResponseBody",
  "GetGuildWidgetSettingsHTTPRequest",
  "GetGuildWidgetSettingsHTTPResponse",
  "GetGuildWidgetSettingsHTTPResponseBody",
  "GetGuildsOnboardingHTTPRequest",
  "GetGuildsOnboardingHTTPResponse",
  "GetGuildsOnboardingHTTPResponseBody",
  "GetInviteTargetUsersHTTPRequest",
  "GetInviteTargetUsersHTTPResponse",
  "GetInviteTargetUsersHTTPResponseBody",
  "GetInviteTargetUsersJobStatusHTTPRequest",
  "GetInviteTargetUsersJobStatusHTTPResponse",
  "GetInviteTargetUsersJobStatusHTTPResponseBody",
  "GetLobbyHTTPRequest",
  "GetLobbyHTTPResponse",
  "GetLobbyHTTPResponseBody",
  "GetLobbyMessagesHTTPRequest",
  "GetLobbyMessagesHTTPResponse",
  "GetLobbyMessagesHTTPResponseBody",
  "GetMessageHTTPRequest",
  "GetMessageHTTPResponse",
  "GetMessageHTTPResponseBody",
  "GetMyApplicationHTTPRequest",
  "GetMyApplicationHTTPResponse",
  "GetMyApplicationHTTPResponseBody",
  "GetMyGuildMemberHTTPRequest",
  "GetMyGuildMemberHTTPResponse",
  "GetMyGuildMemberHTTPResponseBody",
  "GetMyOauth2ApplicationHTTPRequest",
  "GetMyOauth2ApplicationHTTPResponse",
  "GetMyOauth2ApplicationHTTPResponseBody",
  "GetMyOauth2AuthorizationHTTPRequest",
  "GetMyOauth2AuthorizationHTTPResponse",
  "GetMyOauth2AuthorizationHTTPResponseBody",
  "GetMyUserHTTPRequest",
  "GetMyUserHTTPResponse",
  "GetMyUserHTTPResponseBody",
  "GetOpenidConnectUserinfoHTTPRequest",
  "GetOpenidConnectUserinfoHTTPResponse",
  "GetOpenidConnectUserinfoHTTPResponseBody",
  "GetOriginalWebhookMessageHTTPRequest",
  "GetOriginalWebhookMessageHTTPResponse",
  "GetOriginalWebhookMessageHTTPResponseBody",
  "GetPublicKeysHTTPRequest",
  "GetPublicKeysHTTPResponse",
  "GetPublicKeysHTTPResponseBody",
  "GetSelfVoiceStateHTTPRequest",
  "GetSelfVoiceStateHTTPResponse",
  "GetSelfVoiceStateHTTPResponseBody",
  "GetSkuSubscriptionHTTPRequest",
  "GetSkuSubscriptionHTTPResponse",
  "GetSkuSubscriptionHTTPResponseBody",
  "GetSkuSubscriptionsHTTPRequest",
  "GetSkuSubscriptionsHTTPResponse",
  "GetSkuSubscriptionsHTTPResponseBody",
  "GetSoundboardDefaultSoundsHTTPRequest",
  "GetSoundboardDefaultSoundsHTTPResponse",
  "GetSoundboardDefaultSoundsHTTPResponseBody",
  "GetStageInstanceHTTPRequest",
  "GetStageInstanceHTTPResponse",
  "GetStageInstanceHTTPResponseBody",
  "GetStickerHTTPRequest",
  "GetStickerHTTPResponse",
  "GetStickerHTTPResponseBody",
  "GetStickerPackHTTPRequest",
  "GetStickerPackHTTPResponse",
  "GetStickerPackHTTPResponseBody",
  "GetThreadMemberHTTPRequest",
  "GetThreadMemberHTTPResponse",
  "GetThreadMemberHTTPResponseBody",
  "GetUserHTTPRequest",
  "GetUserHTTPResponse",
  "GetUserHTTPResponseBody",
  "GetVoiceStateHTTPRequest",
  "GetVoiceStateHTTPResponse",
  "GetVoiceStateHTTPResponseBody",
  "GetWebhookByTokenHTTPRequest",
  "GetWebhookByTokenHTTPResponse",
  "GetWebhookByTokenHTTPResponseBody",
  "GetWebhookHTTPRequest",
  "GetWebhookHTTPResponse",
  "GetWebhookHTTPResponseBody",
  "GetWebhookMessageHTTPRequest",
  "GetWebhookMessageHTTPResponse",
  "GetWebhookMessageHTTPResponseBody",
  "GuildRoleMemberCountsHTTPRequest",
  "GuildRoleMemberCountsHTTPResponse",
  "GuildRoleMemberCountsHTTPResponseBody",
  "GuildSearchHTTPRequest",
  "GuildSearchHTTPResponse",
  "GuildSearchHTTPResponseBody",
  "InviteResolveHTTPRequest",
  "InviteResolveHTTPResponse",
  "InviteResolveHTTPResponseBody",
  "InviteRevokeHTTPRequest",
  "InviteRevokeHTTPResponse",
  "InviteRevokeHTTPResponseBody",
  "JoinThreadHTTPRequest",
  "JoinThreadHTTPResponse",
  "JoinThreadHTTPResponseBody",
  "LeaveGuildHTTPRequest",
  "LeaveGuildHTTPResponse",
  "LeaveGuildHTTPResponseBody",
  "LeaveLobbyHTTPRequest",
  "LeaveLobbyHTTPResponse",
  "LeaveLobbyHTTPResponseBody",
  "LeaveThreadHTTPRequest",
  "LeaveThreadHTTPResponse",
  "LeaveThreadHTTPResponseBody",
  "ListApplicationCommandsHTTPRequest",
  "ListApplicationCommandsHTTPResponse",
  "ListApplicationCommandsHTTPResponseBody",
  "ListApplicationEmojisHTTPRequest",
  "ListApplicationEmojisHTTPResponse",
  "ListApplicationEmojisHTTPResponseBody",
  "ListAutoModerationRulesHTTPRequest",
  "ListAutoModerationRulesHTTPResponse",
  "ListAutoModerationRulesHTTPResponseBody",
  "ListChannelInvitesHTTPRequest",
  "ListChannelInvitesHTTPResponse",
  "ListChannelInvitesHTTPResponseBody",
  "ListChannelWebhooksHTTPRequest",
  "ListChannelWebhooksHTTPResponse",
  "ListChannelWebhooksHTTPResponseBody",
  "ListGuildApplicationCommandPermissionsHTTPRequest",
  "ListGuildApplicationCommandPermissionsHTTPResponse",
  "ListGuildApplicationCommandPermissionsHTTPResponseBody",
  "ListGuildApplicationCommandsHTTPRequest",
  "ListGuildApplicationCommandsHTTPResponse",
  "ListGuildApplicationCommandsHTTPResponseBody",
  "ListGuildAuditLogEntriesHTTPRequest",
  "ListGuildAuditLogEntriesHTTPResponse",
  "ListGuildAuditLogEntriesHTTPResponseBody",
  "ListGuildBansHTTPRequest",
  "ListGuildBansHTTPResponse",
  "ListGuildBansHTTPResponseBody",
  "ListGuildChannelsHTTPRequest",
  "ListGuildChannelsHTTPResponse",
  "ListGuildChannelsHTTPResponseBody",
  "ListGuildEmojisHTTPRequest",
  "ListGuildEmojisHTTPResponse",
  "ListGuildEmojisHTTPResponseBody",
  "ListGuildIntegrationsHTTPRequest",
  "ListGuildIntegrationsHTTPResponse",
  "ListGuildIntegrationsHTTPResponseBody",
  "ListGuildInvitesHTTPRequest",
  "ListGuildInvitesHTTPResponse",
  "ListGuildInvitesHTTPResponseBody",
  "ListGuildMembersHTTPRequest",
  "ListGuildMembersHTTPResponse",
  "ListGuildMembersHTTPResponseBody",
  "ListGuildRolesHTTPRequest",
  "ListGuildRolesHTTPResponse",
  "ListGuildRolesHTTPResponseBody",
  "ListGuildScheduledEventExceptionUsersHTTPRequest",
  "ListGuildScheduledEventExceptionUsersHTTPResponse",
  "ListGuildScheduledEventExceptionUsersHTTPResponseBody",
  "ListGuildScheduledEventUsersHTTPRequest",
  "ListGuildScheduledEventUsersHTTPResponse",
  "ListGuildScheduledEventUsersHTTPResponseBody",
  "ListGuildScheduledEventsHTTPRequest",
  "ListGuildScheduledEventsHTTPResponse",
  "ListGuildScheduledEventsHTTPResponseBody",
  "ListGuildSoundboardSoundsHTTPRequest",
  "ListGuildSoundboardSoundsHTTPResponse",
  "ListGuildSoundboardSoundsHTTPResponseBody",
  "ListGuildStickersHTTPRequest",
  "ListGuildStickersHTTPResponse",
  "ListGuildStickersHTTPResponseBody",
  "ListGuildTemplatesHTTPRequest",
  "ListGuildTemplatesHTTPResponse",
  "ListGuildTemplatesHTTPResponseBody",
  "ListGuildVoiceRegionsHTTPRequest",
  "ListGuildVoiceRegionsHTTPResponse",
  "ListGuildVoiceRegionsHTTPResponseBody",
  "ListMessageReactionsByEmojiHTTPRequest",
  "ListMessageReactionsByEmojiHTTPResponse",
  "ListMessageReactionsByEmojiHTTPResponseBody",
  "ListMessagesHTTPRequest",
  "ListMessagesHTTPResponse",
  "ListMessagesHTTPResponseBody",
  "ListMyConnectionsHTTPRequest",
  "ListMyConnectionsHTTPResponse",
  "ListMyConnectionsHTTPResponseBody",
  "ListMyGuildsHTTPRequest",
  "ListMyGuildsHTTPResponse",
  "ListMyGuildsHTTPResponseBody",
  "ListMyPrivateArchivedThreadsHTTPRequest",
  "ListMyPrivateArchivedThreadsHTTPResponse",
  "ListMyPrivateArchivedThreadsHTTPResponseBody",
  "ListPinsHTTPRequest",
  "ListPinsHTTPResponse",
  "ListPinsHTTPResponseBody",
  "ListPrivateArchivedThreadsHTTPRequest",
  "ListPrivateArchivedThreadsHTTPResponse",
  "ListPrivateArchivedThreadsHTTPResponseBody",
  "ListPublicArchivedThreadsHTTPRequest",
  "ListPublicArchivedThreadsHTTPResponse",
  "ListPublicArchivedThreadsHTTPResponseBody",
  "ListStickerPacksHTTPRequest",
  "ListStickerPacksHTTPResponse",
  "ListStickerPacksHTTPResponseBody",
  "ListThreadMembersHTTPRequest",
  "ListThreadMembersHTTPResponse",
  "ListThreadMembersHTTPResponseBody",
  "ListVoiceRegionsHTTPRequest",
  "ListVoiceRegionsHTTPResponse",
  "ListVoiceRegionsHTTPResponseBody",
  "PartnerSdkTokenHTTPRequest",
  "PartnerSdkTokenHTTPResponse",
  "PartnerSdkTokenHTTPResponseBody",
  "PartnerSdkUnmergeProvisionalAccountHTTPRequest",
  "PartnerSdkUnmergeProvisionalAccountHTTPResponse",
  "PartnerSdkUnmergeProvisionalAccountHTTPResponseBody",
  "PollExpireHTTPRequest",
  "PollExpireHTTPResponse",
  "PollExpireHTTPResponseBody",
  "PreviewPruneGuildHTTPRequest",
  "PreviewPruneGuildHTTPResponse",
  "PreviewPruneGuildHTTPResponseBody",
  "PruneGuildHTTPRequest",
  "PruneGuildHTTPResponse",
  "PruneGuildHTTPResponseBody",
  "PutGuildsOnboardingHTTPRequest",
  "PutGuildsOnboardingHTTPResponse",
  "PutGuildsOnboardingHTTPResponseBody",
  "SearchGuildMembersHTTPRequest",
  "SearchGuildMembersHTTPResponse",
  "SearchGuildMembersHTTPResponseBody",
  "SendSoundboardSoundHTTPRequest",
  "SendSoundboardSoundHTTPResponse",
  "SendSoundboardSoundHTTPResponseBody",
  "SetChannelPermissionOverwriteHTTPRequest",
  "SetChannelPermissionOverwriteHTTPResponse",
  "SetChannelPermissionOverwriteHTTPResponseBody",
  "SetGuildApplicationCommandPermissionsHTTPRequest",
  "SetGuildApplicationCommandPermissionsHTTPResponse",
  "SetGuildApplicationCommandPermissionsHTTPResponseBody",
  "SyncGuildTemplateHTTPRequest",
  "SyncGuildTemplateHTTPResponse",
  "SyncGuildTemplateHTTPResponseBody",
  "ThreadSearchHTTPRequest",
  "ThreadSearchHTTPResponse",
  "ThreadSearchHTTPResponseBody",
  "TriggerTypingIndicatorHTTPRequest",
  "TriggerTypingIndicatorHTTPResponse",
  "TriggerTypingIndicatorHTTPResponseBody",
  "UnbanUserFromGuildHTTPRequest",
  "UnbanUserFromGuildHTTPResponse",
  "UnbanUserFromGuildHTTPResponseBody",
  "UpdateApplicationCommandHTTPRequest",
  "UpdateApplicationCommandHTTPResponse",
  "UpdateApplicationCommandHTTPResponseBody",
  "UpdateApplicationEmojiHTTPRequest",
  "UpdateApplicationEmojiHTTPResponse",
  "UpdateApplicationEmojiHTTPResponseBody",
  "UpdateApplicationHTTPRequest",
  "UpdateApplicationHTTPResponse",
  "UpdateApplicationHTTPResponseBody",
  "UpdateApplicationRoleConnectionsMetadataHTTPRequest",
  "UpdateApplicationRoleConnectionsMetadataHTTPResponse",
  "UpdateApplicationRoleConnectionsMetadataHTTPResponseBody",
  "UpdateApplicationUserRoleConnectionHTTPRequest",
  "UpdateApplicationUserRoleConnectionHTTPResponse",
  "UpdateApplicationUserRoleConnectionHTTPResponseBody",
  "UpdateAutoModerationRuleHTTPRequest",
  "UpdateAutoModerationRuleHTTPResponse",
  "UpdateAutoModerationRuleHTTPResponseBody",
  "UpdateChannelHTTPRequest",
  "UpdateChannelHTTPResponse",
  "UpdateChannelHTTPResponseBody",
  "UpdateGuildApplicationCommandHTTPRequest",
  "UpdateGuildApplicationCommandHTTPResponse",
  "UpdateGuildApplicationCommandHTTPResponseBody",
  "UpdateGuildEmojiHTTPRequest",
  "UpdateGuildEmojiHTTPResponse",
  "UpdateGuildEmojiHTTPResponseBody",
  "UpdateGuildHTTPRequest",
  "UpdateGuildHTTPResponse",
  "UpdateGuildHTTPResponseBody",
  "UpdateGuildIncidentActionsHTTPRequest",
  "UpdateGuildIncidentActionsHTTPResponse",
  "UpdateGuildIncidentActionsHTTPResponseBody",
  "UpdateGuildMemberHTTPRequest",
  "UpdateGuildMemberHTTPResponse",
  "UpdateGuildMemberHTTPResponseBody",
  "UpdateGuildRoleHTTPRequest",
  "UpdateGuildRoleHTTPResponse",
  "UpdateGuildRoleHTTPResponseBody",
  "UpdateGuildScheduledEventExceptionHTTPRequest",
  "UpdateGuildScheduledEventExceptionHTTPResponse",
  "UpdateGuildScheduledEventExceptionHTTPResponseBody",
  "UpdateGuildScheduledEventHTTPRequest",
  "UpdateGuildScheduledEventHTTPResponse",
  "UpdateGuildScheduledEventHTTPResponseBody",
  "UpdateGuildSoundboardSoundHTTPRequest",
  "UpdateGuildSoundboardSoundHTTPResponse",
  "UpdateGuildSoundboardSoundHTTPResponseBody",
  "UpdateGuildStickerHTTPRequest",
  "UpdateGuildStickerHTTPResponse",
  "UpdateGuildStickerHTTPResponseBody",
  "UpdateGuildTemplateHTTPRequest",
  "UpdateGuildTemplateHTTPResponse",
  "UpdateGuildTemplateHTTPResponseBody",
  "UpdateGuildWelcomeScreenHTTPRequest",
  "UpdateGuildWelcomeScreenHTTPResponse",
  "UpdateGuildWelcomeScreenHTTPResponseBody",
  "UpdateGuildWidgetSettingsHTTPRequest",
  "UpdateGuildWidgetSettingsHTTPResponse",
  "UpdateGuildWidgetSettingsHTTPResponseBody",
  "UpdateInviteTargetUsersHTTPRequest",
  "UpdateInviteTargetUsersHTTPResponse",
  "UpdateInviteTargetUsersHTTPResponseBody",
  "UpdateLobbyMessageExternalModerationMetadataHTTPRequest",
  "UpdateLobbyMessageExternalModerationMetadataHTTPResponse",
  "UpdateLobbyMessageExternalModerationMetadataHTTPResponseBody",
  "UpdateMessageHTTPRequest",
  "UpdateMessageHTTPResponse",
  "UpdateMessageHTTPResponseBody",
  "UpdateMyApplicationHTTPRequest",
  "UpdateMyApplicationHTTPResponse",
  "UpdateMyApplicationHTTPResponseBody",
  "UpdateMyGuildMemberHTTPRequest",
  "UpdateMyGuildMemberHTTPResponse",
  "UpdateMyGuildMemberHTTPResponseBody",
  "UpdateMyUserHTTPRequest",
  "UpdateMyUserHTTPResponse",
  "UpdateMyUserHTTPResponseBody",
  "UpdateOriginalWebhookMessageHTTPRequest",
  "UpdateOriginalWebhookMessageHTTPResponse",
  "UpdateOriginalWebhookMessageHTTPResponseBody",
  "UpdateSelfVoiceStateHTTPRequest",
  "UpdateSelfVoiceStateHTTPResponse",
  "UpdateSelfVoiceStateHTTPResponseBody",
  "UpdateStageInstanceHTTPRequest",
  "UpdateStageInstanceHTTPResponse",
  "UpdateStageInstanceHTTPResponseBody",
  "UpdateUserMessageExternalModerationMetadataHTTPRequest",
  "UpdateUserMessageExternalModerationMetadataHTTPResponse",
  "UpdateUserMessageExternalModerationMetadataHTTPResponseBody",
  "UpdateVoiceChannelStatusHTTPRequest",
  "UpdateVoiceChannelStatusHTTPResponse",
  "UpdateVoiceChannelStatusHTTPResponseBody",
  "UpdateVoiceStateHTTPRequest",
  "UpdateVoiceStateHTTPResponse",
  "UpdateVoiceStateHTTPResponseBody",
  "UpdateWebhookByTokenHTTPRequest",
  "UpdateWebhookByTokenHTTPResponse",
  "UpdateWebhookByTokenHTTPResponseBody",
  "UpdateWebhookHTTPRequest",
  "UpdateWebhookHTTPResponse",
  "UpdateWebhookHTTPResponseBody",
  "UpdateWebhookMessageHTTPRequest",
  "UpdateWebhookMessageHTTPResponse",
  "UpdateWebhookMessageHTTPResponseBody",
  "UploadApplicationAttachmentHTTPRequest",
  "UploadApplicationAttachmentHTTPResponse",
  "UploadApplicationAttachmentHTTPResponseBody",
)
