from micro.discord._schema import normalize


def test_normalizer_prunes_inlines_and_adds_discriminator() -> None:
  schema = {
    "$ref": "#/definitions/Payload",
    "definitions": {
      "Payload": {
        "oneOf": [
          {"$ref": "#/definitions/FieldDataOne"},
          {"$ref": "#/definitions/_DataPayloadTwo"},
        ]
      },
      "FieldDataOne": {
        "type": "object",
        "properties": {"op": {"const": 1}},
        "required": ["op"],
      },
      "_DataPayloadTwo": {
        "type": "object",
        "properties": {"op": {"const": 2}},
        "required": ["op"],
      },
      "Unused": {"type": "string"},
    },
  }

  stats = normalize(schema)

  assert stats == {
    "removed": 1,
    "inlined": 2,
    "tuples": 0,
    "discriminators": 1,
  }
  assert schema["definitions"] == {
    "Payload": {
      "oneOf": [
        {
          "type": "object",
          "properties": {"op": {"const": 1}},
          "required": ["op"],
        },
        {
          "type": "object",
          "properties": {"op": {"const": 2}},
          "required": ["op"],
        },
      ],
      "discriminator": {"propertyName": "op"},
    }
  }


def test_normalizer_rejects_ambiguous_discriminator_values() -> None:
  schema = {
    "oneOf": [
      {
        "type": "object",
        "properties": {"kind": {"const": "same"}},
        "required": ["kind"],
      },
      {
        "type": "object",
        "properties": {"kind": {"const": "same"}},
        "required": ["kind"],
      },
    ]
  }

  stats = normalize(schema)

  assert stats["discriminators"] == 0
  assert "discriminator" not in schema


def test_normalizer_resolves_encoded_definition_references() -> None:
  schema = {
    "$ref": "#/definitions/Wrapper%3CData%3E",
    "definitions": {
      "Wrapper<Data>": {"$ref": "#/definitions/Data"},
      "Data": {"type": "string"},
    },
  }

  stats = normalize(schema)

  assert stats["removed"] == 0
  assert set(schema["definitions"]) == {"Wrapper<Data>", "Data"}


def test_normalizer_combines_homogeneous_tuple_lengths() -> None:
  schema = {
    "oneOf": [
      {
        "type": "array",
        "prefixItems": [{"type": "string"}, {"type": "string"}],
        "additionalItems": False,
      },
      {
        "type": "array",
        "prefixItems": [{"type": "string"}],
        "additionalItems": False,
      },
    ]
  }

  stats = normalize(schema)

  assert stats["tuples"] == 2
  assert schema == {
    "type": "array",
    "items": {"type": "string"},
    "minItems": 1,
    "maxItems": 2,
  }
