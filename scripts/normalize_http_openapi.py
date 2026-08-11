import argparse
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

_METHODS = frozenset(("delete", "get", "patch", "post", "put"))


def _pascal(value: str) -> str:
  return "".join(part.capitalize() for part in value.split("_"))


def _resolve(document: dict[str, Any], value: dict[str, Any]) -> dict[str, Any]:
  reference = value.get("$ref")
  if not isinstance(reference, str):
    return value
  resolved: Any = document
  for part in reference.removeprefix("#/").split("/"):
    resolved = resolved[part.replace("~1", "/").replace("~0", "~")]
  if not isinstance(resolved, dict):
    raise TypeError(f"OpenAPI reference does not resolve to an object: {reference}")
  return resolved


def normalize(source: Path, output: Path) -> None:
  document = json.loads(source.read_text())
  _normalize_binary(document)
  schemas = document.setdefault("components", {}).setdefault("schemas", {})
  for path_item in document["paths"].values():
    inherited = path_item.get("parameters", [])
    for method, operation in path_item.items():
      if method not in _METHODS:
        continue
      operation_id = operation["operationId"]
      parameters = []
      for raw in [*inherited, *operation.get("parameters", [])]:
        parameter = _resolve(document, raw)
        if parameter.get("in") == "path":
          parameters.append(parameter)
      if not parameters:
        continue
      name = f"{_pascal(operation_id)}ParametersPath"
      schemas[name] = {
        "type": "object",
        "properties": {
          parameter["name"]: deepcopy(parameter["schema"]) for parameter in parameters
        },
        "required": [parameter["name"] for parameter in parameters],
        "additionalProperties": False,
      }
  output.write_text(json.dumps(document, separators=(",", ":")))


def _normalize_binary(value: Any) -> None:
  if isinstance(value, dict):
    if value.get("contentEncoding") == "binary":
      value.pop("contentEncoding")
      value["format"] = "binary"
    for child in value.values():
      _normalize_binary(child)
  elif isinstance(value, list):
    for child in value:
      _normalize_binary(child)


def main() -> None:
  parser = argparse.ArgumentParser()
  parser.add_argument("source", type=Path)
  parser.add_argument("output", type=Path)
  arguments = parser.parse_args()
  normalize(arguments.source, arguments.output)


if __name__ == "__main__":
  main()
