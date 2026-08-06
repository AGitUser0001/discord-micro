"""Normalize generated Gateway JSON Schema before producing Python models."""

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path
from typing import Any
from urllib.parse import unquote

type Json = dict[str, Any] | list[Any] | str | int | float | bool | None


def _definition_name(reference: str) -> str | None:
  for prefix in ("#/definitions/", "#/components/schemas/"):
    if reference.startswith(prefix):
      return unquote(reference[len(prefix) :]).replace("~1", "/").replace("~0", "~")
  return None


def _definitions(schema: dict[str, Any]) -> dict[str, Json]:
  definitions = schema.get("definitions")
  if isinstance(definitions, dict):
    return definitions
  components = schema.get("components")
  if isinstance(components, dict) and isinstance(components.get("schemas"), dict):
    return components["schemas"]
  return {}


def _references(value: Json) -> list[str]:
  found: list[str] = []
  if isinstance(value, dict):
    reference = value.get("$ref")
    if isinstance(reference, str) and (name := _definition_name(reference)):
      found.append(name)
    for child in value.values():
      found.extend(_references(child))
  elif isinstance(value, list):
    for child in value:
      found.extend(_references(child))
  return found


def _prune_unreachable(schema: dict[str, Any]) -> int:
  definitions = _definitions(schema)
  if not definitions:
    return 0
  root = (
    schema["schema"]
    if isinstance(schema.get("schema"), dict)
    else {key: value for key, value in schema.items() if key != "definitions"}
  )
  pending = _references(root)
  reachable: set[str] = set()
  while pending:
    name = pending.pop()
    if name in reachable or name not in definitions:
      continue
    reachable.add(name)
    pending.extend(_references(definitions[name]))

  removed = len(definitions) - len(reachable)
  retained = {
    name: definition for name, definition in definitions.items() if name in reachable
  }
  if "definitions" in schema:
    schema["definitions"] = retained
  else:
    schema["components"]["schemas"] = retained
  return removed


def _object_shape(
  value: Json,
  definitions: dict[str, Json],
  seen: frozenset[str] = frozenset(),
) -> tuple[dict[str, Json], set[str]] | None:
  if not isinstance(value, dict):
    return None
  reference = value.get("$ref")
  if isinstance(reference, str) and (name := _definition_name(reference)):
    if name in seen or name not in definitions:
      return None
    return _object_shape(definitions[name], definitions, seen | {name})

  properties = value.get("properties", {})
  required = set(value.get("required", []))
  if not isinstance(properties, dict):
    return None
  merged: dict[str, Json] = dict(properties)
  for part in value.get("allOf", []):
    shape = _object_shape(part, definitions, seen)
    if shape is None:
      return None
    part_properties, part_required = shape
    merged.update(part_properties)
    required.update(part_required)
  return merged, required


def _literal(property_schema: Json) -> str | int | None:
  if not isinstance(property_schema, dict):
    return None
  value = property_schema.get("const")
  if isinstance(value, str | int) and not isinstance(value, bool):
    return value
  values = property_schema.get("enum")
  if (
    isinstance(values, list)
    and len(values) == 1
    and isinstance(values[0], str | int)
    and not isinstance(values[0], bool)
  ):
    return values[0]
  return None


def _normalize_homogeneous_tuples(schema: dict[str, Any]) -> int:
  normalized = 0

  def tuple_array(value: Json) -> tuple[Json, int] | None:
    if not isinstance(value, dict) or value.get("type") != "array":
      return None
    prefix = value.get("prefixItems")
    if not isinstance(prefix, list) or not prefix:
      return None
    first = prefix[0]
    if any(item != first for item in prefix[1:]):
      return None
    return first, len(prefix)

  def visit(value: Json) -> None:
    nonlocal normalized
    if isinstance(value, list):
      for child in value:
        visit(child)
      return
    if not isinstance(value, dict):
      return
    alternatives = value.get("oneOf")
    if isinstance(alternatives, list) and alternatives:
      tuples = [tuple_array(alternative) for alternative in alternatives]
      if all(item is not None for item in tuples):
        complete = [item for item in tuples if item is not None]
        element = complete[0][0]
        lengths = sorted(length for _, length in complete)
        if all(item == element for item, _ in complete) and lengths == list(
          range(lengths[0], lengths[-1] + 1)
        ):
          value.pop("oneOf")
          value.update(
            {
              "type": "array",
              "items": deepcopy(element),
              "minItems": lengths[0],
              "maxItems": lengths[-1],
            }
          )
          normalized += len(complete)
          return

    for child in value.values():
      visit(child)

    if (tuple_info := tuple_array(value)) is not None:
      element, length = tuple_info
      value.pop("prefixItems")
      value.pop("additionalItems", None)
      value.update(
        {
          "items": deepcopy(element),
          "minItems": length,
          "maxItems": length,
        }
      )
      normalized += 1

  visit(schema)
  return normalized


def _add_discriminators(schema: dict[str, Any]) -> int:
  definitions = _definitions(schema)
  added = 0

  def visit(value: Json) -> None:
    nonlocal added
    if isinstance(value, list):
      for child in value:
        visit(child)
      return
    if not isinstance(value, dict):
      return

    for keyword in ("oneOf", "anyOf"):
      branches = value.get(keyword)
      if not isinstance(branches, list) or len(branches) < 2:
        continue
      shapes = [_object_shape(branch, definitions) for branch in branches]
      if any(shape is None for shape in shapes):
        continue
      complete_shapes = [shape for shape in shapes if shape is not None]
      common = set.intersection(*(required for _, required in complete_shapes))
      for field in ("t", "op", *sorted(common - {"t", "op"})):
        if field not in common:
          continue
        literals = [
          _literal(properties.get(field)) for properties, _ in complete_shapes
        ]
        if None not in literals and len(set(literals)) == len(literals):
          value["discriminator"] = {"propertyName": field}
          added += 1
          break

    for child in value.values():
      visit(child)

  visit(schema)
  return added


def normalize(schema: dict[str, Any]) -> dict[str, int]:
  removed = _prune_unreachable(schema)
  tuples = _normalize_homogeneous_tuples(schema)
  discriminators = _add_discriminators(schema)
  return {
    "removed": removed,
    "tuples": tuples,
    "discriminators": discriminators,
  }


def main() -> None:
  parser = argparse.ArgumentParser()
  parser.add_argument("schema", type=Path)
  arguments = parser.parse_args()
  schema = json.loads(arguments.schema.read_text())
  stats = normalize(schema)
  arguments.schema.write_text(json.dumps(schema, separators=(",", ":")))
  print(
    "Normalized Gateway schema: "
    f"removed {stats['removed']} unreachable definitions, "
    f"normalized {stats['tuples']} homogeneous tuple schemas, "
    f"added {stats['discriminators']} discriminators."
  )


if __name__ == "__main__":
  main()
