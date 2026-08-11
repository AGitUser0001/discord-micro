import json
import subprocess
import sys
from pathlib import Path

from pydantic import RootModel

from micro.discord.http_operations import HTTP_OPERATIONS, GeneratedDiscordHTTPClient


def test_every_generated_operation_has_a_physical_client_method() -> None:
  assert len(HTTP_OPERATIONS) >= 200
  assert all(hasattr(GeneratedDiscordHTTPClient, name) for name in HTTP_OPERATIONS)
  assert HTTP_OPERATIONS["create_message"].path == "/channels/{channel_id}/messages"
  assert HTTP_OPERATIONS["create_message"].path_fields == ("channel_id",)
  assert all(
    issubclass(operation.response_body_model, RootModel)
    for operation in HTTP_OPERATIONS.values()
  )


def test_operation_generator_combines_path_query_and_body_inputs(
  tmp_path: Path,
) -> None:
  source = tmp_path / "openapi.json"
  normalized = tmp_path / "normalized.json"
  models = tmp_path / "models.py"
  requests = tmp_path / "requests.py"
  operations = tmp_path / "operations.py"
  source.write_text(
    json.dumps(
      {
        "openapi": "3.1.0",
        "info": {"title": "test", "version": "1"},
        "paths": {
          "/things/{thing_id}": {
            "parameters": [
              {
                "name": "thing_id",
                "in": "path",
                "required": True,
                "schema": {"type": "string"},
              }
            ],
            "post": {
              "operationId": "create_thing",
              "parameters": [
                {"name": "wait", "in": "query", "schema": {"type": "boolean"}}
              ],
              "requestBody": {
                "required": True,
                "content": {
                  "application/json": {"schema": {"$ref": "#/components/schemas/Thing"}}
                },
              },
              "responses": {"201": {"description": "created"}},
            },
          }
        },
        "components": {"schemas": {"Thing": {"type": "object", "properties": {}}}},
      }
    )
  )
  subprocess.run(
    [
      sys.executable,
      "scripts/normalize_http_openapi.py",
      str(source),
      str(normalized),
    ],
    check=True,
  )
  models.write_text(
    "class Thing: pass\n"
    "class CreateThingParametersPath: pass\n"
    "class CreateThingParametersQuery: pass\n"
  )
  subprocess.run(
    [
      sys.executable,
      "scripts/generate_http_operations.py",
      str(normalized),
      str(models),
      str(requests),
      str(operations),
    ],
    check=True,
  )
  document = json.loads(normalized.read_text())
  schema = document["components"]["schemas"]["CreateThingParametersPath"]
  assert schema["required"] == ["thing_id"]
  assert set(schema["properties"]) == {"thing_id"}
  generated_requests = requests.read_text()
  assert "path: http.CreateThingParametersPath" in generated_requests
  assert "query: http.CreateThingParametersQuery | None = None" in generated_requests
  assert "body: http.Thing" in generated_requests
  assert "class CreateThingHTTPResponseBody(RootModel[JsonValue])" in generated_requests
  assert "type CreateThing" not in generated_requests
  assert "async def create_thing(" in operations.read_text()
