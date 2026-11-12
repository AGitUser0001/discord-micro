"""Every interaction handler is called the same way: `(ctx, interaction, ...its own arguments)`."""

from collections.abc import Callable
from typing import Any


def call(
  handler: Callable[..., Any], interaction: Any, *args: Any, **kwargs: Any
) -> Any:
  """Call a handler with the `Context`, the `Interaction`, then its own arguments."""
  return handler(interaction.context, interaction, *args, **kwargs)
