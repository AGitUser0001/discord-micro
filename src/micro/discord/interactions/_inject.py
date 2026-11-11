"""Handlers ask for what they need by annotation: `(ctx: Context, interaction: Interaction)`."""

import annotationlib
import inspect
from collections.abc import Callable
from typing import Any

_PLANS: dict[Callable[..., Any], tuple[str, ...]] = {}


def _kind(annotation: object) -> str:
  """`"context"` or `"interaction"` for an annotation naming those classes (by identity,
  so an alias works; by name when the annotation could not be resolved), else `""`."""
  from ._application import Context
  from ._context import Interaction

  if annotation is Context:
    return "context"
  if annotation is Interaction:
    return "interaction"
  return {"Context": "context", "Interaction": "interaction"}.get(_name(annotation), "")


def _name(annotation: object) -> str:
  if isinstance(annotation, str):
    return annotation.rpartition(".")[2].strip("'\" ")
  return getattr(annotation, "__name__", None) or getattr(
    annotation, "__forward_arg__", ""
  )


def leading(handler: Callable[..., Any]) -> tuple[str, ...]:
  """Which of `"context"` and `"interaction"` a handler's first parameters ask for, in
  order. A first parameter that is annotated with neither is the interaction."""
  if handler not in _PLANS:
    try:
      parameters = list(
        inspect.signature(
          handler, annotation_format=annotationlib.Format.FORWARDREF
        ).parameters.values()
      )
    except TypeError, ValueError:
      parameters = []
    found: list[str] = []
    for parameter in parameters[:2]:
      kind = _kind(parameter.annotation)
      if not kind:
        break
      found.append(kind)
    _PLANS[handler] = tuple(found) or ("interaction",)
  return _PLANS[handler]


def call(
  handler: Callable[..., Any], interaction: Any, *args: Any, **kwargs: Any
) -> Any:
  """Call a handler with what it asked for first, then its own arguments."""
  asked = [
    interaction.context if kind == "context" else interaction
    for kind in leading(handler)
  ]
  return handler(*asked, *args, **kwargs)
