"""Ed25519 signature verification (RFC 8032) in plain Python.

Only what Discord's HTTP interactions need: verifying a signature against a
public key. Variable time is fine because nothing here is secret.
"""

import hashlib

_P = 2**255 - 19
_L = 2**252 + 27742317777372353535851937790883648493
_D = -121665 * pow(121666, -1, _P) % _P
_I = pow(2, (_P - 1) // 4, _P)  # a square root of -1

type _Point = tuple[int, int, int, int]  # extended coordinates (X, Y, Z, T)


def _add(a: _Point, b: _Point) -> _Point:
  x1, y1, z1, t1 = a
  x2, y2, z2, t2 = b
  p = _P
  aa, bb = (y1 - x1) * (y2 - x2) % p, (y1 + x1) * (y2 + x2) % p
  cc, dd = 2 * t1 * t2 * _D % p, 2 * z1 * z2 % p
  e, f, g, h = bb - aa, dd - cc, dd + cc, bb + aa
  return e * f % p, g * h % p, f * g % p, e * h % p


def _multiply(scalar: int, point: _Point) -> _Point:
  result: _Point = (0, 1, 1, 0)
  while scalar:
    if scalar & 1:
      result = _add(result, point)
    point = _add(point, point)
    scalar >>= 1
  return result


def _decode(data: bytes) -> _Point | None:
  if len(data) != 32:
    return None
  y = int.from_bytes(data, "little")
  sign, y = y >> 255, y & (2**255 - 1)
  if y >= _P:
    return None
  x2 = (y * y - 1) * pow(_D * y * y + 1, -1, _P) % _P
  x = pow(x2, (_P + 3) // 8, _P)
  if (x * x - x2) % _P:
    x = x * _I % _P
  if (x * x - x2) % _P:
    return None
  if x == 0 and sign:
    return None
  if x & 1 != sign:
    x = _P - x
  return x, y, 1, x * y % _P


_BASE_Y = 4 * pow(5, -1, _P) % _P
_BASE = _decode(_BASE_Y.to_bytes(32, "little"))
assert _BASE is not None


def _equal(a: _Point, b: _Point) -> bool:
  return (a[0] * b[2] - b[0] * a[2]) % _P == 0 and (a[1] * b[2] - b[1] * a[2]) % _P == 0


def verify(public_key: bytes, message: bytes, signature: bytes) -> bool:
  """Whether `signature` is `public_key`'s valid Ed25519 signature of `message`."""
  if len(signature) != 64:
    return False
  a = _decode(public_key)
  r = _decode(signature[:32])
  s = int.from_bytes(signature[32:], "little")
  if a is None or r is None or s >= _L:
    return False
  k = (
    int.from_bytes(
      hashlib.sha512(signature[:32] + public_key + message).digest(), "little"
    )
    % _L
  )
  assert _BASE is not None
  return _equal(_multiply(s, _BASE), _add(r, _multiply(k, a)))
