"""Colours as Discord wants them: one integer, `0xRRGGBB`, with helpers.

embed("Done", colour=Colour.GREEN)
embed("Done", colour="#57f287")             # a string, a tuple, a name or an int all work
Colour.from_rgb(88, 101, 242).lighten(0.2)
"""

import colorsys
import re
from typing import Any, ClassVar, Self

from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema

type ColourLike = Colour | int | str | tuple[int, int, int]
"""Anything `Colour.parse` understands: a number, `"#5865f2"`, `"blurple"`, or `(r, g, b)`."""

_HEX = re.compile(r"#?([0-9a-fA-F]{3}|[0-9a-fA-F]{6})")


class Colour(int):
  """A colour: an `int` from 0 to 0xFFFFFF, so it goes anywhere Discord wants a colour."""

  __slots__ = ()

  BLURPLE: ClassVar[Colour]
  GREEN: ClassVar[Colour]
  YELLOW: ClassVar[Colour]
  FUCHSIA: ClassVar[Colour]
  RED: ClassVar[Colour]
  WHITE: ClassVar[Colour]
  DARK: ClassVar[Colour]
  BLUE: ClassVar[Colour]
  TEAL: ClassVar[Colour]
  PURPLE: ClassVar[Colour]
  ORANGE: ClassVar[Colour]
  GOLD: ClassVar[Colour]
  GREY: ClassVar[Colour]
  MAPLE: ClassVar[Colour]

  def __new__(cls, value: int = 0) -> Self:
    if not 0 <= value <= 0xFFFFFF:
      raise ValueError(f"A colour is 0 to 0xFFFFFF, not {value:#x}.")
    return super().__new__(cls, value)

  @classmethod
  def __get_pydantic_core_schema__(
    cls, source: Any, handler: GetCoreSchemaHandler
  ) -> core_schema.CoreSchema:
    """Pydantic fields typed `Colour` validate to a `Colour` and dump as the plain int."""
    return core_schema.no_info_after_validator_function(
      cls,
      core_schema.int_schema(ge=0, le=0xFFFFFF),
      serialization=core_schema.plain_serializer_function_ser_schema(int),
    )

  # Building ---------------------------------------------------------------------

  @classmethod
  def from_rgb(cls, red: int, green: int, blue: int) -> Self:
    """From red, green and blue, each 0 to 255."""
    if not all(0 <= part <= 255 for part in (red, green, blue)):
      raise ValueError("Red, green and blue are each 0 to 255.")
    return cls(red << 16 | green << 8 | blue)

  @classmethod
  def from_hsv(cls, hue: float, saturation: float, value: float) -> Self:
    """From hue in degrees (0 to 360) and saturation and value (0 to 1)."""
    red, green, blue = colorsys.hsv_to_rgb((hue % 360) / 360, saturation, value)
    return cls.from_rgb(round(red * 255), round(green * 255), round(blue * 255))

  @classmethod
  def from_hex(cls, text: str) -> Self:
    """From `"#5865f2"`, `"5865f2"` or the short `"#58f"`."""
    found = _HEX.fullmatch(text.strip())
    if found is None:
      raise ValueError(f"{text!r} is not a hex colour like #5865f2.")
    digits = found.group(1)
    if len(digits) == 3:
      digits = "".join(digit * 2 for digit in digits)
    return cls(int(digits, 16))

  @classmethod
  def parse(cls, value: ColourLike) -> Self:
    """Turn a number, hex string, colour name (`"blurple"`) or `(r, g, b)` into a `Colour`."""
    if isinstance(value, tuple):
      return cls.from_rgb(*value)
    if isinstance(value, str):
      named = _NAMES.get(value.strip().lower().replace(" ", "").replace("-", "_"))
      return cls(named) if named is not None else cls.from_hex(value)
    return cls(int(value))

  # Reading ----------------------------------------------------------------------

  @property
  def r(self) -> int:
    """The red part, 0 to 255."""
    return self >> 16 & 0xFF

  @property
  def g(self) -> int:
    """The green part, 0 to 255."""
    return self >> 8 & 0xFF

  @property
  def b(self) -> int:
    """The blue part, 0 to 255."""
    return self & 0xFF

  @property
  def rgb(self) -> tuple[int, int, int]:
    """`(red, green, blue)`."""
    return self.r, self.g, self.b

  @property
  def hsv(self) -> tuple[float, float, float]:
    """`(hue in degrees, saturation, value)`."""
    hue, saturation, value = colorsys.rgb_to_hsv(
      self.r / 255, self.g / 255, self.b / 255
    )
    return hue * 360, saturation, value

  @property
  def hex(self) -> str:
    """The `"#rrggbb"` form."""
    return f"#{int(self):06x}"

  # Changing (a colour never changes: these return a new one) -------------------------

  def mix(self, other: ColourLike, weight: float = 0.5) -> Colour:
    """This colour moved `weight` (0 to 1) of the way toward `other`."""
    target = Colour.parse(other)
    return Colour.from_rgb(
      *(round(a + (b - a) * weight) for a, b in zip(self.rgb, target.rgb, strict=True))
    )

  def lighten(self, amount: float = 0.2) -> Colour:
    """Mixed `amount` (0 to 1) toward white."""
    return self.mix(Colour.WHITE, amount)

  def darken(self, amount: float = 0.2) -> Colour:
    """Mixed `amount` (0 to 1) toward black."""
    return self.mix(0, amount)

  def __repr__(self) -> str:
    return f"Colour({self.hex})"

  def __str__(self) -> str:
    return self.hex


_NAMES = {
  "blurple": 0x5865F2,
  "green": 0x57F287,
  "yellow": 0xFEE75C,
  "fuchsia": 0xEB459E,
  "red": 0xED4245,
  "white": 0xFFFFFF,
  "dark": 0x23272A,
  "blue": 0x3498DB,
  "teal": 0x1ABC9C,
  "purple": 0x9B59B6,
  "orange": 0xE67E22,
  "gold": 0xF1C40F,
  "grey": 0x95A5A6,
  "gray": 0x95A5A6,
  "maple": 0xD52B1E,
}
for _name, _value in _NAMES.items():
  if _name != "gray":
    setattr(Colour, _name.upper(), Colour(_value))
