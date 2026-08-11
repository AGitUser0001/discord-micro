import argparse
import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

_METHODS = ("delete", "get", "patch", "post", "put")


def _model_name(operation_id: str) -> str:
  return (
    "DiscordHTTP"
    + "".join(part.capitalize() for part in operation_id.split("_"))
    + "Input"
  )


def _media_name(content_type: str) -> str:
  return "".join(part.capitalize() for part in re.split(r"[^A-Za-z0-9]+", content_type))


def _resolve(document: dict[str, Any], value: dict[str, Any]) -> dict[str, Any]:
  reference = value.get("$ref")
  if not isinstance(reference, str):
    return value
  if not reference.startswith("#/"):
    raise ValueError(f"Only local OpenAPI references are supported: {reference}")
  resolved: Any = document
  for part in reference[2:].split("/"):
    resolved = resolved[part.replace("~1", "/").replace("~0", "~")]
  if not isinstance(resolved, dict):
    raise TypeError(f"OpenAPI reference does not resolve to an object: {reference}")
  return resolved


def generate(source: Path, normalized: Path, output: Path) -> None:
  document = json.loads(source.read_text())
  _normalize_binary_schemas(document)
  schemas = document.setdefault("components", {}).setdefault("schemas", {})
  operations: list[dict[str, Any]] = []
  operation_ids: set[str] = set()

  for path, path_item in document["paths"].items():
    inherited = path_item.get("parameters", [])
    for method in _METHODS:
      if method not in path_item:
        continue
      operation = path_item[method]
      operation_id = operation.get("operationId")
      if not isinstance(operation_id, str) or not operation_id.isidentifier():
        raise ValueError(f"{method.upper()} {path} has no valid operationId")
      if operation_id in operation_ids:
        raise ValueError(f"Duplicate Discord operationId: {operation_id}")
      operation_ids.add(operation_id)

      properties: dict[str, Any] = {}
      required: list[str] = []
      locations: dict[str, list[str]] = {"path": [], "query": [], "header": []}
      for raw_parameter in [*inherited, *operation.get("parameters", [])]:
        parameter = _resolve(document, raw_parameter)
        name = parameter["name"]
        location = parameter["in"]
        if location not in locations:
          continue
        if name in properties:
          raise ValueError(f"Duplicate parameter {name!r} in {operation_id}")
        properties[name] = deepcopy(parameter.get("schema", {}))
        if "description" in parameter:
          properties[name].setdefault("description", parameter["description"])
        locations[location].append(name)
        if parameter.get("required", False):
          required.append(name)

      content = operation.get("requestBody", {}).get("content", {})
      content_types = list(content)
      if content:
        body_schemas = []
        for content_type, media in content.items():
          body_schema = deepcopy(media["schema"])
          if "$ref" not in body_schema:
            body_name = (
              f"{_model_name(operation_id)[:-5]}{_media_name(content_type)}Body"
            )
            schemas[body_name] = body_schema
            body_schema = {"$ref": f"#/components/schemas/{body_name}"}
          body_schemas.append(body_schema)
        unique: list[dict[str, Any]] = []
        for schema in body_schemas:
          if schema not in unique:
            unique.append(schema)
        properties["body"] = unique[0] if len(unique) == 1 else {"anyOf": unique}
        preferred_content_type = (
          "application/json" if "application/json" in content else content_types[0]
        )
        properties["content_type"] = {
          "type": "string",
          "default": preferred_content_type,
        }
        if operation.get("requestBody", {}).get("required", False):
          required.append("body")

      model_name = _model_name(operation_id)
      input_schema: dict[str, Any] = {
        "type": "object",
        "properties": properties,
        "additionalProperties": False,
      }
      if required:
        input_schema["required"] = required
      schemas[model_name] = input_schema
      success_statuses = sorted(
        int(status)
        for status in operation.get("responses", {})
        if status.isdecimal() and 200 <= int(status) < 300
      )
      operations.append(
        {
          "id": operation_id,
          "model": model_name,
          "method": method.upper(),
          "path": path,
          "path_fields": locations["path"],
          "query_fields": locations["query"],
          "header_fields": locations["header"],
          "content_types": content_types,
          "success_statuses": success_statuses,
        }
      )

  normalized.write_text(json.dumps(document, separators=(",", ":")))
  output.write_text(_render(operations))


def _normalize_binary_schemas(value: Any) -> None:
  if isinstance(value, dict):
    if value.get("contentEncoding") == "binary":
      value.pop("contentEncoding")
      value["format"] = "binary"
    for child in value.values():
      _normalize_binary_schemas(child)
  elif isinstance(value, list):
    for child in value:
      _normalize_binary_schemas(child)


def _render(operations: list[dict[str, Any]]) -> str:
  literal = "\n".join(f'  "{item["id"]}",' for item in operations)
  definitions = []
  methods = []
  for item in operations:
    definitions.append(
      f'''  "{item["id"]}": DiscordHTTPOperation(
    id="{item["id"]}",
    method="{item["method"]}",
    path="{item["path"]}",
    input_model=models.{item["model"]},
    path_fields={tuple(item["path_fields"])!r},
    query_fields={tuple(item["query_fields"])!r},
    header_fields={tuple(item["header_fields"])!r},
    content_types={tuple(item["content_types"])!r},
    success_statuses={tuple(item["success_statuses"])!r},
  ),'''
    )
    methods.append(
      f'''  async def {item["id"]}(
    self, request: models.{item["model"]}
  ) -> ResponseT:
    return await self._request_operation("{item["id"]}", request)
'''
    )
  return f'''# Generated from Discord's OpenAPI specification by scripts/generate_http_operations.py.
# Do not edit directly.

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel

from .models import http as models

type DiscordOperationId = Literal[
{literal}
]


@dataclass(frozen=True, slots=True)
class DiscordHTTPOperation:
  id: DiscordOperationId
  method: str
  path: str
  input_model: type[BaseModel]
  path_fields: tuple[str, ...]
  query_fields: tuple[str, ...]
  header_fields: tuple[str, ...]
  content_types: tuple[str, ...]
  success_statuses: tuple[int, ...]


HTTP_OPERATIONS: dict[DiscordOperationId, DiscordHTTPOperation] = {{
{chr(10).join(definitions)}
}}


class GeneratedDiscordHTTPClient[ResponseT]:
  async def _request_operation(
    self, operation: DiscordOperationId, request: BaseModel
  ) -> ResponseT:
    raise NotImplementedError

{chr(10).join(methods)}


__all__ = (
  "DiscordHTTPOperation",
  "DiscordOperationId",
  "GeneratedDiscordHTTPClient",
  "HTTP_OPERATIONS",
)
'''


def main() -> None:
  parser = argparse.ArgumentParser()
  parser.add_argument("source", type=Path)
  parser.add_argument("normalized", type=Path)
  parser.add_argument("output", type=Path)
  arguments = parser.parse_args()
  generate(arguments.source, arguments.normalized, arguments.output)


if __name__ == "__main__":
  main()
