"""Fetch a file from a URL Discord gave you: an avatar, an attachment, a sticker.

    data = (await download(user.display_avatar.url)).unwrap()
    attachment = message.attachments[0]
    match await download(attachment.url):
      case Ok(data): ...
      case Err(error): ...                 # error.status is the HTTP status, if there was one

The result is the file's bytes. Like every call that can fail in an expected way it comes
back as a `Result` (`micro.result`), so a missing file is a value you can handle.
"""

import asyncio
from dataclasses import dataclass
from typing import Any
from weakref import WeakKeyDictionary

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


_clients: WeakKeyDictionary[asyncio.AbstractEventLoop, Any] = WeakKeyDictionary()


def _client() -> Any:
  """The process's one download client for this event loop, so connections are reused."""
  import httpx2

  loop = asyncio.get_running_loop()
  client = _clients.get(loop)
  if client is None or client.is_closed:
    client = httpx2.AsyncClient(follow_redirects=True, timeout=None)
    _clients[loop] = client
  return client


async def download(
  url: str, *, timeout: float | None = None, max_size: int | None = None
) -> Result[bytes, DownloadError]:
  """The bytes at `url`: an `asset.url`, an `attachment.url`, any address.

  Redirects are followed. By default there is no time or size limit, so a large file
  simply takes as long as it takes; ask for one when the address is not one you trust.

  Args:
    url: Where to fetch from.
    timeout: Seconds the server may stay silent (to connect, or between pieces of the
      file) before giving up. None waits as long as it takes.
    max_size: The most bytes to accept. A file that announces or turns out to be larger
      is abandoned without reading the rest. None accepts any size.

  Returns:
    `Ok(bytes)`, or `Err(DownloadError)` if the server answered with an error status,
    could not be reached, timed out, or the file is larger than `max_size`.
  """
  import httpx2

  try:
    async with _client().stream("GET", url, timeout=timeout) as response:
      if response.status_code >= 400:
        return Err(
          DownloadError(url, response.status_code, f"HTTP {response.status_code}")
        )
      announced = response.headers.get("content-length", "")
      if max_size is not None and announced.isdecimal() and int(announced) > max_size:
        return Err(DownloadError(url, None, f"larger than {max_size} bytes"))
      chunks: list[bytes] = []
      total = 0
      async for chunk in response.aiter_bytes():
        total += len(chunk)
        if max_size is not None and total > max_size:
          return Err(DownloadError(url, None, f"larger than {max_size} bytes"))
        chunks.append(chunk)
  except httpx2.TransportError as error:
    return Err(DownloadError(url, None, str(error) or type(error).__name__))
  return Ok(b"".join(chunks))
