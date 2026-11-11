"""Handlers ask for what they need by annotation: `(ctx: Context, message: Message)`.

A handler's leading parameters annotated with an injectable (`Context`) are filled in from
the service, and its payload parameter annotated with a convertible type (`Message`, `Member`)
gets the payload converted to it. Anything else behaves as before: the handler gets the
payload as the schema defines it. Discord's types register themselves (`micro.discord`).
"""

import annotationlib
import importlib
import inspect
import json
import types
import typing
from collections.abc import Callable
from contextlib import suppress
from typing import Any

from micro import subjects

_FACTORIES: dict[Any, Callable[[Any], Any]] = {}
_CONVERTERS: dict[Any, Callable[[Any, Any], Any]] = {}
_PLANS: dict[Callable[..., Any], tuple[tuple[Any, ...], Any, bool]] = {}
_loaded = False
NO_PAYLOAD: Any = object()
"""Pass as the payload to call a handler that takes only what it asks for."""


def injectable(kind: type, factory: Callable[[Any], Any]) -> None:
  """Handlers whose leading parameter is annotated `kind` get `factory(service)`."""
  _FACTORIES[kind] = factory


def convertible(kind: type, converter: Callable[[Any, Any], Any]) -> None:
  """A handler whose payload parameter is annotated `kind` gets `converter(payload, service)`."""
  _CONVERTERS[kind] = converter


def _load() -> None:
  global _loaded
  if not _loaded:
    _loaded = True
    with suppress(ImportError):
      importlib.import_module("micro.discord._bindings")


def _candidates(annotation: object) -> list[object]:
  """What an annotation may name: itself, or each part of `X | None` (also as a string)."""
  if isinstance(annotation, str) or hasattr(annotation, "__forward_arg__"):
    text = annotation if isinstance(annotation, str) else annotation.__forward_arg__  # type: ignore[attr-defined]
    return [part.strip().strip("'\"") for part in text.split("|")]
  if typing.get_origin(annotation) in (typing.Union, types.UnionType):
    return list(typing.get_args(annotation))
  return [annotation]


def _match(annotation: object, registry: dict[Any, Any]) -> Any:
  """The registered type an annotation names: the class itself (so an alias works), or,
  for an annotation that could not be resolved, a class of that name. `X | None` names X."""
  for candidate in _candidates(annotation):
    if candidate in registry:
      return candidate
    name = candidate.rpartition(".")[2] if isinstance(candidate, str) else ""
    found = (
      next((kind for kind in registry if kind.__name__ == name), None) if name else None
    )
    if found is not None:
      return found
  return None


def _plan(handler: Callable[..., Any]) -> tuple[tuple[Any, ...], Any, bool]:
  if handler not in _PLANS:
    _load()
    try:
      parameters = list(
        inspect.signature(
          handler, annotation_format=annotationlib.Format.FORWARDREF
        ).parameters.values()
      )
    except TypeError, ValueError:
      parameters = []
    asked: list[Any] = []
    for parameter in parameters:
      kind = _match(parameter.annotation, _FACTORIES)
      if kind is None:
        break
      asked.append(kind)
    rest = parameters[len(asked) :]
    changed = len(rest) >= 2 and rest[0].name == "before"
    anchor = rest[1] if changed else (rest[0] if rest else None)
    payload = _match(anchor.annotation, _CONVERTERS) if anchor is not None else None
    _PLANS[handler] = (tuple(asked), payload, changed)
  return _PLANS[handler]


async def call_handler(
  service: Any,
  handler: Callable[..., Any],
  payload: Any = NO_PAYLOAD,
  message: Any = None,
) -> Any:
  """Call an event or work handler with what it asked for, then its payload (or, for a
  handler whose parameters are `before, after`, the object as it was and as it is)."""
  asked, convert, changed = _plan(handler)
  arguments = [_FACTORIES[kind](service) for kind in asked]
  if payload is NO_PAYLOAD:
    return await handler(*arguments)
  if changed:
    raw = (getattr(message, "headers", None) or {}).get(subjects.BEFORE_HEADER)
    earlier = json.loads(raw) if raw else None
    if convert is not None:
      if earlier is not None:
        earlier = _CONVERTERS[convert](earlier, service)
      payload = _CONVERTERS[convert](payload, service)
    return await handler(*arguments, earlier, payload)
  if convert is not None:
    payload = _CONVERTERS[convert](payload, service)
  return await handler(*arguments, payload)
