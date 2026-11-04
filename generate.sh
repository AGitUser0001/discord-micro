#!/bin/sh
set -eu

repository=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
temporary=$(mktemp -d "${TMPDIR:-/tmp}/micro-discord-models.XXXXXX")

cleanup() {
  rm -rf -- "$temporary"
}
trap cleanup EXIT HUP INT TERM

cd "$temporary"
npm init --yes >/dev/null
npm install --no-save --package-lock=false \
  @types/node@latest \
  discord-api-types@latest \
  ttsc@latest \
  typia@latest \
  typescript@latest

application_declarations="$temporary/node_modules/discord-api-types/payloads/v10/application.d.ts"
gateway_entrypoint="$temporary/gateway.ts"
gateway_schema="$temporary/gateway.schema.json"
http_schema="$temporary/openapi.json"
normalized_http_schema="$temporary/openapi.normalized.json"
gateway_models="$temporary/gateway.py"
http_models="$temporary/http.py"
http_operations="$temporary/http_operations.py"
http_requests="$temporary/http_requests.py"
event_schemas="$repository/src/micro/schemas/events.py"

node -e '
const fs = require("node:fs");
const file = process.argv[1];
const before = fs.readFileSync(file, "utf8");
const needle = "[string, string?, string?, string?, string?]";
const replacement = "[string] | [string, string] | [string, string, string] | [string, string, string, string] | [string, string, string, string, string]";
const count = before.split(needle).length - 1;
if (count !== 1) {
  throw new Error(`expected one application tags tuple, found ${count}`);
}
fs.writeFileSync(file, before.replace(needle, replacement));
' "$application_declarations"

printf '%s\n' \
  '{"compilerOptions":{"strict":true,"module":"nodenext","moduleResolution":"nodenext","target":"esnext","types":["node"],"plugins":[{"transform":"typia/lib/transform"}]}}' \
  >"$temporary/tsconfig.json"

printf '%s\n' \
  'import { writeFileSync } from "node:fs";' \
  'import typia from "typia";' \
  'import type { GatewayDispatchPayload, GatewayReceivePayload, GatewaySendPayload } from "discord-api-types/gateway/v10";' \
  'type GatewayNonDispatchReceivePayload = Exclude<GatewayReceivePayload, GatewayDispatchPayload>;' \
  'const generated = typia.json.schemas<[GatewayDispatchPayload, GatewayNonDispatchReceivePayload, GatewaySendPayload]>();' \
  'const [dispatch, receive, send] = generated.schemas;' \
  'const schemas = generated.components.schemas ??= {};' \
  'schemas.GatewayDispatchPayload ??= dispatch;' \
  'schemas.GatewayNonDispatchReceivePayload ??= receive;' \
  'schemas.GatewaySendPayload ??= send;' \
  'schemas.GatewayReceivePayload = { oneOf: [{ $ref: "#/components/schemas/GatewayDispatchPayload" }, { $ref: "#/components/schemas/GatewayNonDispatchReceivePayload" }] };' \
  'schemas.GatewayPayload = { oneOf: [{ $ref: "#/components/schemas/GatewayReceivePayload" }, { $ref: "#/components/schemas/GatewaySendPayload" }] };' \
  'writeFileSync("gateway.schema.json", JSON.stringify({ version: generated.version, components: generated.components, schema: { $ref: "#/components/schemas/GatewayPayload" } }));' \
  >"$gateway_entrypoint"

"$temporary/node_modules/.bin/ttsx" "$gateway_entrypoint"

uv run --project "$repository" python "$repository/src/micro/discord/_schema.py" \
  "$gateway_schema"

node -e '
const fs = require("node:fs");
const file = process.argv[1];
const generated = JSON.parse(fs.readFileSync(file, "utf8"));
fs.writeFileSync(file, JSON.stringify({
  openapi: "3.1.0",
  info: { title: "Discord Gateway", version: "10" },
  paths: {},
  components: generated.components,
}));
' "$gateway_schema"

curl --fail --location --silent --show-error \
  --output "$http_schema" \
  https://raw.githubusercontent.com/discord/discord-api-spec/main/specs/openapi.json

uv run --project "$repository" python \
  "$repository/scripts/normalize_http_openapi.py" \
  "$http_schema" "$normalized_http_schema"

generate_models() {
  uv run --project "$repository" datamodel-codegen \
    --input "$1" \
    --input-file-type openapi \
    --openapi-scopes schemas \
    --output "$2" \
    --output-model-type pydantic_v2.BaseModel \
    --target-python-version 3.14 \
    --disable-timestamp \
    --strict-refs \
    --use-standard-collections \
    --use-union-operator \
    --use-annotated \
    --extra-fields allow
}

generate_models "$gateway_schema" "$gateway_models"
uv run --project "$repository" datamodel-codegen \
  --input "$normalized_http_schema" \
  --input-file-type openapi \
  --openapi-scopes schemas paths parameters requestbodies \
  --use-operation-id-as-name \
  --use-status-code-in-response-name \
  --output "$http_models" \
  --output-model-type pydantic_v2.BaseModel \
  --base-class micro.discord._model.DiscordModel \
  --target-python-version 3.14 \
  --disable-timestamp \
  --use-standard-collections \
  --use-union-operator \
  --use-annotated \
  --extra-fields allow

uv run --project "$repository" python \
  "$repository/scripts/generate_http_operations.py" \
  "$normalized_http_schema" "$http_models" "$http_requests" "$http_operations"

models="$repository/src/micro/discord/models"
uv run --project "$repository" ruff check --fix "$http_requests" "$http_operations"
uv run --project "$repository" ruff format "$http_requests" "$http_operations"
# Split each generated module into small modules behind a lazy index, so a
# process imports only the models it uses.
mkdir -p "$models"
uv run --project "$repository" python "$repository/scripts/split_models.py" \
  "$gateway_models" "$models/gateway" --package micro.discord.models.gateway
uv run --project "$repository" python "$repository/scripts/split_models.py" \
  "$http_models" "$models/http" --package micro.discord.models.http
uv run --project "$repository" python "$repository/scripts/split_models.py" \
  "$http_requests" "$models/http_requests" --package micro.discord.models.http_requests \
  --rewrite "from . import http=>from micro.discord.models import http"
install -m 0644 "$http_operations" \
  "$repository/src/micro/discord/http_operations.py"
uv run --project "$repository" python "$repository/scripts/generate_events.py" \
  "$gateway_models" "$event_schemas"

printf 'Generated %s, %s, %s, %s, and %s\n' \
  "$models/gateway/" \
  "$models/http/" \
  "$models/http_requests/" \
  "$repository/src/micro/discord/http_operations.py" \
  "$event_schemas"
