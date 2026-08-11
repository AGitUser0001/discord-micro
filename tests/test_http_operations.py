import json
import subprocess
import sys
from pathlib import Path

from micro.discord.http_operations import HTTP_OPERATIONS, GeneratedDiscordHTTPClient


def test_every_generated_operation_has_a_physical_client_method() -> None:
  assert len(HTTP_OPERATIONS) >= 200
  assert all(hasattr(GeneratedDiscordHTTPClient, name) for name in HTTP_OPERATIONS)
  assert HTTP_OPERATIONS["create_message"].path == "/channels/{channel_id}/messages"
  assert HTTP_OPERATIONS["create_message"].path_fields == ("channel_id",)


def test_operation_generator_combines_path_query_and_body_inputs(
  tmp_path: Path,
) -> None:
  source = tmp_path / "openapi.json"
  normalized = tmp_path / "normalized.json"
  generated = tmp_path / "operations.py"
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
      "scripts/generate_http_operations.py",
      str(source),
      str(normalized),
      str(generated),
    ],
    check=True,
  )
  document = json.loads(normalized.read_text())
  schema = document["components"]["schemas"]["DiscordHTTPCreateThingInput"]
  assert schema["required"] == ["thing_id", "body"]
  assert set(schema["properties"]) == {"thing_id", "wait", "body", "content_type"}
  assert 'async def create_thing(' in generated.read_text()
