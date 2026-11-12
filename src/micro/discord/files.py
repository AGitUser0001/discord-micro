"""Fetch a file from a URL Discord gave you: an avatar, an attachment, a sticker.

    data = (await download(user.display_avatar.url)).unwrap()
    attachment = message.attachments[0]
    match await download(attachment.url):
      case Ok(data): ...
      case Err(error): ...                 # error.status is the HTTP status, if there was one

The result is the file's bytes. Like every call that can fail in an expected way it comes
back as a `Result` (`micro.result`), so a missing file is a value you can handle.
"""

from dataclasses import dataclass

from micro.errors import MicroError
from micro.result import Err, Ok, Result


@dataclass(eq=False)
class DownloadError(MicroError):
  """A file could not be downloaded: the server refused (`status`) or could not be reached."""

  url: str
  status: int | None = None
  """The HTTP status, or None if the server could not be reached."""
  reason: str = ""

  def __str__(self) -> str:
    return f"Could not download {self.url}: {self.reason or self.status}"


async def download(url: str) -> Result[bytes, DownloadError]:
  """The bytes at `url`: an `asset.url`, an `attachment.url`, any address.

  Redirects are followed and there is no size or time limit, so a large file simply
  takes as long as it takes.

  Returns:
    `Ok(bytes)`, or `Err(DownloadError)` if the server answered with an error status or
    could not be reached.
  """
  import httpx2

  address = url
  try:
    async with httpx2.AsyncClient(follow_redirects=True, timeout=None) as client:
      response = await client.get(address)
  except httpx2.TransportError as error:
    return Err(DownloadError(address, None, str(error) or type(error).__name__))
  if response.status_code >= 400:
    return Err(
      DownloadError(address, response.status_code, f"HTTP {response.status_code}")
    )
  return Ok(response.content)
