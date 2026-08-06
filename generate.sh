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
  discord-api-types@latest \
  ts-json-schema-generator@latest \
  typescript@latest

gateway_declarations="$temporary/node_modules/discord-api-types/gateway/v10.d.ts"
gateway_entrypoint="$temporary/gateway.ts"
gateway_schema="$temporary/gateway.schema.json"
http_schema="$temporary/openapi.json"
gateway_models="$temporary/gateway.py"
http_models="$temporary/http.py"

printf '%s\n' \
  "import type { GatewayReceivePayload, GatewaySendPayload } from '$gateway_declarations';" \
  "export type GatewayPayload = GatewayReceivePayload | GatewaySendPayload;" \
  >"$gateway_entrypoint"

"$temporary/node_modules/.bin/ts-json-schema-generator" \
  --path "$gateway_entrypoint" \
  --type GatewayPayload \
  --expose export \
  --additional-properties \
  --out "$gateway_schema"

curl --fail --location --silent --show-error \
  --output "$http_schema" \
  https://raw.githubusercontent.com/discord/discord-api-spec/main/specs/openapi.json

generate_models() {
  uv run --project "$repository" datamodel-codegen \
    --input "$1" \
    --input-file-type "$2" \
    --output "$3" \
    --output-model-type pydantic_v2.BaseModel \
    --target-python-version 3.14 \
    --disable-timestamp \
    --use-standard-collections \
    --use-union-operator \
    --use-annotated \
    --extra-fields allow
}

generate_models "$gateway_schema" jsonschema "$gateway_models"
uv run --project "$repository" datamodel-codegen \
  --input "$http_schema" \
  --input-file-type openapi \
  --openapi-scopes schemas \
  --output "$http_models" \
  --output-model-type pydantic_v2.BaseModel \
  --target-python-version 3.14 \
  --disable-timestamp \
  --use-standard-collections \
  --use-union-operator \
  --use-annotated \
  --extra-fields allow

models="$repository/src/micro/discord/models"
mkdir -p "$models"
install -m 0644 "$gateway_models" "$models/gateway.py"
install -m 0644 "$http_models" "$models/http.py"

printf 'Generated %s and %s\n' \
  "$models/gateway.py" \
  "$models/http.py"
