import os
from collections.abc import Mapping, Sequence
from typing import cast

from database import ApacheAgeExecutor
from graphql import FieldNode, GraphQLError, get_argument_values

from micro.service import JsonValue
from micro.store import (
  CompiledOperation,
  GraphCompiler,
  GraphQLRequest,
  GraphResult,
  GraphStatement,
  Store,
  StoreModule,
)

BASE_SCHEMA = """
  type Query { _micro: Boolean }
  type Mutation { _micro: Boolean }
"""


class UnavailableCompiler:
  def compile(self, request: GraphQLRequest) -> CompiledOperation:
    raise GraphQLError("The selected field is not implemented by an active module.")


class ApplicationCompiler:
  def compile(self, request: GraphQLRequest) -> CompiledOperation:
    selections = request.operation.selection_set.selections
    if len(selections) != 1 or not isinstance(selections[0], FieldNode):
      raise GraphQLError("This example accepts one root field per operation.")
    field = selections[0]
    root = request.schema.get_root_type(request.operation.operation)
    if root is None or field.name.value not in root.fields:
      raise GraphQLError("The selected root field is unavailable.")
    arguments = get_argument_values(
      root.fields[field.name.value], field, dict(request.variables)
    )
    name = cast(str, arguments["name"])

    if field.name.value == "greeting":
      statement = GraphStatement(
        "MATCH (greeting:Greeting) WHERE greeting.name = $name "
        "RETURN greeting.name AS name, greeting.message AS message",
        {"name": name},
        ("name", "message"),
      )
      nullable = True
    elif field.name.value == "saveGreeting":
      message = cast(str, arguments["message"])
      statement = GraphStatement(
        "INSERT (:Greeting {name: $name, message: $message}) "
        "RETURN $name AS name, $message AS message",
        {"name": name, "message": message},
        ("name", "message"),
      )
      nullable = False
    else:
      raise GraphQLError("The selected root field has no graph mapping.")

    def shape(result: GraphResult) -> Mapping[str, JsonValue]:
      value: JsonValue
      if result.rows:
        value = dict(result.rows[0])
      elif nullable:
        value = None
      else:
        raise GraphQLError("The greeting was not stored.")
      return {field.alias.value if field.alias else field.name.value: value}

    return CompiledOperation(statement, shape)


class ApplicationModules:
  def compose(
    self,
    base: GraphCompiler,
    modules: Sequence[StoreModule],
  ) -> GraphCompiler:
    operations = {
      operation
      for module in modules
      for operation in module.configuration.get("operations", [])
      if isinstance(operation, str)
    }
    if operations != {"greeting", "saveGreeting"}:
      raise ValueError("The example received an unsupported store module.")
    return ApplicationCompiler()


executor = ApacheAgeExecutor(
  os.environ.get(
    "MICRO_AGE_URL",
    "postgresql://micro:micro@127.0.0.1:5455/micro",
  )
)
store = Store(
  BASE_SCHEMA,
  compiler=UnavailableCompiler(),
  executor=executor,
  module_composer=ApplicationModules(),
)
