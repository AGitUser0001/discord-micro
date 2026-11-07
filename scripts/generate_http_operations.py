import argparse
import ast
import json
from pathlib import Path
from typing import Any

_METHODS = ("delete", "get", "patch", "post", "put")


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


def _schema_reference(schema: dict[str, Any]) -> str | None:
  reference = schema.get("$ref")
  return reference.rpartition("/")[2] if isinstance(reference, str) else None


def generate(
  source: Path, models_source: Path, requests_output: Path, operations_output: Path
) -> None:
  document = json.loads(source.read_text())
  classes = {
    node.name
    for node in ast.parse(models_source.read_text()).body
    if isinstance(node, ast.ClassDef)
  }
  operations = []
  for path, path_item in document["paths"].items():
    inherited = path_item.get("parameters", [])
    for method in _METHODS:
      if method not in path_item:
        continue
      operation = path_item[method]
      operation_id = operation["operationId"]
      pascal = _pascal(operation_id)
      parameters = [
        _resolve(document, item)
        for item in [*inherited, *operation.get("parameters", [])]
      ]
      path_fields = tuple(
        item["name"] for item in parameters if item.get("in") == "path"
      )
      query_fields = tuple(
        item["name"] for item in parameters if item.get("in") == "query"
      )
      header_fields = tuple(
        item["name"] for item in parameters if item.get("in") == "header"
      )
      path_model = f"{pascal}ParametersPath" if path_fields else None
      query_model = f"{pascal}ParametersQuery" if query_fields else None
      header_model = f"{pascal}ParametersHeader" if header_fields else None
      for model in (path_model, query_model, header_model):
        if model is not None and model not in classes:
          raise ValueError(f"datamodel-code-generator did not emit {model}")

      content = operation.get("requestBody", {}).get("content", {})
      body_model = _body_model(operation_id, content, classes)
      response_models = _response_models(document, pascal, operation, classes)
      success_statuses = tuple(
        sorted(
          int(status)
          for status in operation.get("responses", {})
          if status.isdecimal() and 200 <= int(status) < 300
        )
      )
      operations.append(
        {
          "id": operation_id,
          "pascal": pascal,
          "method": method.upper(),
          "path": path,
          "path_fields": path_fields,
          "query_fields": query_fields,
          "header_fields": header_fields,
          "path_model": path_model,
          "query_model": query_model,
          "header_model": header_model,
          "body_model": body_model,
          "body_required": operation.get("requestBody", {}).get("required", False),
          "content_types": tuple(content),
          "response_models": response_models,
          "success_statuses": success_statuses,
        }
      )
  requests_output.write_text(_render_requests(operations))
  operations_output.write_text(_render_operations(operations))


def _body_model(
  operation_id: str, content: dict[str, Any], classes: set[str]
) -> str | None:
  if not content:
    return None
  candidate = f"{_pascal(operation_id)}Request"
  if candidate in classes:
    return candidate
  references = {
    reference
    for media in content.values()
    if (reference := _schema_reference(media["schema"])) is not None
  }
  if len(references) == 1:
    return references.pop()
  raise ValueError(f"Cannot identify generated request body model for {operation_id}")


def _response_models(
  document: dict[str, Any],
  pascal: str,
  operation: dict[str, Any],
  classes: set[str],
) -> tuple[str, ...]:
  models: list[str] = []
  for status, raw_response in operation.get("responses", {}).items():
    response = _resolve(document, raw_response)
    for media in response.get("content", {}).values():
      candidate = f"{pascal}Response{status}" if status.isdecimal() else None
      reference = _schema_reference(media["schema"])
      model = candidate if candidate in classes else reference
      if model is not None and model in classes and model not in models:
        models.append(model)
  return tuple(models)


def _render_requests(operations: list[dict[str, Any]]) -> str:
  definitions = []
  exports = []
  for item in operations:
    request_name = f'{item["pascal"]}HTTPRequest'
    response_body_name = f'{item["pascal"]}HTTPResponseBody'
    response_name = f'{item["pascal"]}HTTPResponse'
    fields = []
    if item["path_model"]:
      fields.append(f'  path: http.{item["path_model"]}')
    if item["query_model"]:
      fields.append(f'  query: http.{item["query_model"]} | None = None')
    if item["header_model"]:
      fields.append(f'  headers: http.{item["header_model"]} | None = None')
    if item["body_model"]:
      optional = "" if item["body_required"] else " | None = None"
      fields.append(f'  body: http.{item["body_model"]}{optional}')
      default_content = (
        "application/json"
        if "application/json" in item["content_types"]
        else item["content_types"][0]
      )
      fields.append(f'  content_type: str = {default_content!r}')
    if not fields:
      fields.append("  pass")
    body_types = " | ".join(f'http.{name}' for name in item["response_models"])
    if not body_types:
      body_types = "JsonValue"
    definitions.append(
      f'''class {request_name}(DiscordModel):
{chr(10).join(fields)}


class {response_body_name}(RootModel[{body_types}]):
  pass


class {response_name}(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: {response_body_name} | None = None
  raw_body: bytes
'''
    )
    exports.extend((request_name, response_body_name, response_name))
  rendered_exports = "\n".join(f'  "{name}",' for name in exports)
  return f'''# Generated from Discord's OpenAPI specification. Do not edit directly.

from pydantic import JsonValue, RootModel

from micro.discord._model import DiscordModel

from . import http


{chr(10).join(definitions)}

__all__ = (
{rendered_exports}
)
'''


def _render_operations(operations: list[dict[str, Any]]) -> str:
  literal = "\n".join(f'  "{item["id"]}",' for item in operations)
  definitions = []
  methods = []
  for item in operations:
    request_name = f'{item["pascal"]}HTTPRequest'
    response_name = f'{item["pascal"]}HTTPResponse'
    response_body_name = f'{item["pascal"]}HTTPResponseBody'
    definitions.append(
      f'''  "{item["id"]}": DiscordHTTPOperation(
    id="{item["id"]}",
    method="{item["method"]}",
    path="{item["path"]}",
    request="{request_name}",
    response="{response_name}",
    response_body="{response_body_name}",
    path_fields={item["path_fields"]!r},
    query_fields={item["query_fields"]!r},
    header_fields={item["header_fields"]!r},
    content_types={item["content_types"]!r},
    success_statuses={item["success_statuses"]!r},
  ),'''
    )
    methods.append(
      f'''  async def {item["id"]}(
    self, request: requests.{request_name}
  ) -> requests.{response_name}:
    response = await self._request_operation("{item["id"]}", request)
    if not isinstance(response, requests.{response_name}):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response
'''
    )
  return f'''# Generated from Discord's OpenAPI specification. Do not edit directly.

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, RootModel

from .models import http_requests as requests

type DiscordOperationId = Literal[
{literal}
]


@dataclass(frozen=True, slots=True)
class DiscordHTTPOperation:
  """One operation; its models are imported only when first used."""

  id: DiscordOperationId
  method: str
  path: str
  request: str
  response: str
  response_body: str
  path_fields: tuple[str, ...]
  query_fields: tuple[str, ...]
  header_fields: tuple[str, ...]
  content_types: tuple[str, ...]
  success_statuses: tuple[int, ...]

  @property
  def request_model(self) -> type[BaseModel]:
    """The generated Pydantic model of the whole request (path, query, headers, body)."""
    return getattr(requests, self.request)

  @property
  def response_model(self) -> type[BaseModel]:
    """The model the operation returns, or None."""
    return getattr(requests, self.response)

  @property
  def response_body_model(self) -> type[RootModel]:
    """The model of the success body, or None."""
    return getattr(requests, self.response_body)


HTTP_OPERATIONS: dict[DiscordOperationId, DiscordHTTPOperation] = {{
{chr(10).join(definitions)}
}}


class GeneratedDiscordHTTPClient:
  async def _request_operation(
    self, operation: DiscordOperationId, request: BaseModel
  ) -> BaseModel:
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
  parser.add_argument("models_source", type=Path)
  parser.add_argument("requests_output", type=Path)
  parser.add_argument("operations_output", type=Path)
  arguments = parser.parse_args()
  generate(
    arguments.source,
    arguments.models_source,
    arguments.requests_output,
    arguments.operations_output,
  )


if __name__ == "__main__":
  main()
