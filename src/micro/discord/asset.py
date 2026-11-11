"""A picture on Discord's CDN: an avatar, a server icon, a banner.

    user.avatar                      # an Asset, or None if the user set none
    user.avatar.url                  # https://cdn.discordapp.com/avatars/<id>/<hash>.png
    user.avatar.with_size(256).url   # ...?size=256
    user.display_avatar.url          # the avatar, or the default one Discord shows
    str(guild.icon)                  # the URL as well

Animated pictures (a hash starting `a_`) are GIFs, the rest PNGs; `with_format` changes
it. An `Asset` is the hash and where it lives; it is sent back as the bare hash.
"""

from dataclasses import dataclass, replace
from typing import Any, Self

from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema

CDN = "https://cdn.discordapp.com"


@dataclass(frozen=True, slots=True)
class Asset:
  """One CDN picture."""

  path: str
  """Where it lives below the CDN, e.g. `avatars/<user id>`."""
  key: str
  """Its hash (or, for a default avatar, its number)."""
  size: int | None = None
  """A power of two from 16 to 4096, or None for the original size."""
  format: str | None = None
  """`png`, `jpg`, `webp` or `gif`; None picks GIF if animated, else PNG."""

  @property
  def animated(self) -> bool:
    """Whether it moves (Discord marks those hashes with `a_`)."""
    return self.key.startswith("a_")

  @property
  def url(self) -> str:
    """The picture's address."""
    extension = self.format or ("gif" if self.animated else "png")
    query = f"?size={self.size}" if self.size else ""
    return f"{CDN}/{self.path}/{self.key}.{extension}{query}"

  def with_size(self, size: int | None) -> Self:
    """The same picture at another size (None: the original)."""
    return replace(self, size=size)

  def with_format(self, format: str | None) -> Self:
    """The same picture in another file format (None: GIF if animated, else PNG)."""
    return replace(self, format=format)

  def __str__(self) -> str:
    return self.url

  @classmethod
  def __get_pydantic_core_schema__(
    cls, source: Any, handler: GetCoreSchemaHandler
  ) -> core_schema.CoreSchema:
    return core_schema.no_info_plain_validator_function(
      _validated,
      serialization=core_schema.plain_serializer_function_ser_schema(
        lambda asset: asset.key
      ),
    )


def _validated(value: Any) -> Asset:
  if isinstance(value, Asset):
    return value
  raise ValueError("an Asset is built from the object it belongs to")


__all__ = ("CDN", "Asset")
