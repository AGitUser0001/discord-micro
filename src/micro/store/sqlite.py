"""An embedded, disk-backed, schemaless graph executor on SQLite.

The graph lives in one file: nodes (label, identity, JSON properties), edges
(label, source, target, JSON properties), and large property values (files, big JSON) in a side
table so node rows stay small. Many store processes on one machine can share
the file (WAL mode); RAM holds only SQLite's page cache. It executes exactly
the ISO GQL subset Micro's compiler emits and rejects anything else clearly.
For other scales, implement `GraphExecutor` for your database.
"""

import asyncio
import json
import sqlite3
from collections.abc import Iterator, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from graphglot import ast
from graphglot.dialect import Dialect
from pydantic import JsonValue

from ._store import (
  GraphBackendError,
  GraphBatch,
  GraphBatchResult,
  GraphLayout,
  GraphResult,
  GraphStatement,
)

LARGE_VALUE = 4096
"""Encoded property values longer than this (bytes) are stored out of line."""

_LARGE_MARKER = "\x00micro:large"
_SCHEMA = """
CREATE TABLE IF NOT EXISTS nodes (
  id INTEGER PRIMARY KEY,
  label TEXT NOT NULL,
  micro_id TEXT,
  props TEXT NOT NULL DEFAULT '{}'
);
CREATE UNIQUE INDEX IF NOT EXISTS nodes_identity ON nodes(label, micro_id);
CREATE TABLE IF NOT EXISTS edges (
  id INTEGER PRIMARY KEY,
  label TEXT NOT NULL,
  src INTEGER NOT NULL REFERENCES nodes(id),
  dst INTEGER NOT NULL REFERENCES nodes(id),
  props TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS edges_out ON edges(src, label);
CREATE INDEX IF NOT EXISTS edges_in ON edges(dst, label);
CREATE TABLE IF NOT EXISTS large_values (
  node INTEGER NOT NULL REFERENCES nodes(id),
  key TEXT NOT NULL,
  value BLOB NOT NULL,
  PRIMARY KEY (node, key)
);
CREATE TABLE IF NOT EXISTS layouts (
  revision INTEGER PRIMARY KEY,
  definition TEXT NOT NULL
);
"""


class Unsupported(GraphBackendError):
  def __init__(self, what: str) -> None:
    super().__init__(f"The SQLite graph does not support {what}.", code="INVALID")


@dataclass(eq=False)
class _Node:
  id: int
  label: str
  micro_id: str | None
  props: dict[str, Any]
  deleted: bool = False


@dataclass(eq=False)
class _Edge:
  id: int
  label: str
  src: int
  dst: int
  props: dict[str, Any] = field(default_factory=dict)
  deleted: bool = False


type _Row = dict[str, _Node | _Edge | None]


@dataclass
class _Run:
  """One statement's execution against an open transaction."""

  db: sqlite3.Connection
  params: Mapping[str, JsonValue]
  nodes: dict[int, _Node] = field(default_factory=dict)

  # Storage -----------------------------------------------------------------------

  def node(self, node_id: int) -> _Node:
    cached = self.nodes.get(node_id)
    if cached is not None:
      return cached
    row = self.db.execute(
      "SELECT id, label, micro_id, props FROM nodes WHERE id = ?", (node_id,)
    ).fetchone()
    return self._remember(row)

  def _remember(self, row: tuple[Any, ...]) -> _Node:
    cached = self.nodes.get(row[0])
    if cached is not None:
      return cached
    node = _Node(row[0], row[1], row[2], json.loads(row[3]))
    self.nodes[node.id] = node
    return node

  def by_label(self, label: str, micro_id: Any = ...) -> list[_Node]:
    if micro_id is ...:
      rows = self.db.execute(
        "SELECT id, label, micro_id, props FROM nodes WHERE label = ? ORDER BY id",
        (label,),
      ).fetchall()
    else:
      rows = self.db.execute(
        "SELECT id, label, micro_id, props FROM nodes WHERE label = ? AND micro_id = ?",
        (label, None if micro_id is None else str(micro_id)),
      ).fetchall()
    return [node for node in map(self._remember, rows) if not node.deleted]

  def edges(self, node: _Node, label: str, outgoing: bool) -> list[_Edge]:
    column, other = ("src", "dst") if outgoing else ("dst", "src")
    rows = self.db.execute(
      f"SELECT id, label, src, dst, props FROM edges WHERE {column} = ? AND label = ? ORDER BY id",
      (node.id, label),
    ).fetchall()
    del other
    return [_Edge(row[0], row[1], row[2], row[3], json.loads(row[4])) for row in rows]

  def get(self, node: _Node, key: str) -> Any:
    if node.deleted:
      return None
    if key == "_micro_id":
      return node.micro_id
    value = node.props.get(key)
    if value == _LARGE_MARKER:
      row = self.db.execute(
        "SELECT value FROM large_values WHERE node = ? AND key = ?", (node.id, key)
      ).fetchone()
      value = json.loads(row[0]) if row else None
    return value

  def create(self, label: str, props: dict[str, Any]) -> _Node:
    micro_id = props.pop("_micro_id", None)
    cursor = self.db.execute(
      "INSERT INTO nodes (label, micro_id, props) VALUES (?, ?, '{}')",
      (label, None if micro_id is None else str(micro_id)),
    )
    node = _Node(cursor.lastrowid or 0, label, micro_id, {})
    self.nodes[node.id] = node
    self.update(node, props)
    return node

  def update(self, node: _Node, values: Mapping[str, Any]) -> None:
    if node.deleted or not values:
      return
    for key, value in values.items():
      if key == "_micro_id":
        node.micro_id = None if value is None else str(value)
        self.db.execute(
          "UPDATE nodes SET micro_id = ? WHERE id = ?", (node.micro_id, node.id)
        )
        continue
      encoded = json.dumps(value, separators=(",", ":"))
      if len(encoded) > LARGE_VALUE:
        self.db.execute(
          "INSERT OR REPLACE INTO large_values (node, key, value) VALUES (?, ?, ?)",
          (node.id, key, encoded.encode()),
        )
        node.props[key] = _LARGE_MARKER
      else:
        if node.props.get(key) == _LARGE_MARKER:
          self.db.execute(
            "DELETE FROM large_values WHERE node = ? AND key = ?", (node.id, key)
          )
        if value is None:
          node.props.pop(key, None)
        else:
          node.props[key] = value
    self.db.execute(
      "UPDATE nodes SET props = ? WHERE id = ?",
      (json.dumps(node.props, separators=(",", ":")), node.id),
    )

  def update_edge(self, edge: _Edge, values: Mapping[str, Any]) -> None:
    """Set (or, for None, remove) properties of an edge."""
    for key, value in values.items():
      if value is None:
        edge.props.pop(key, None)
      else:
        edge.props[key] = value
    self.db.execute(
      "UPDATE edges SET props = ? WHERE id = ?",
      (json.dumps(edge.props, separators=(",", ":")), edge.id),
    )

  def connect(
    self,
    label: str,
    source: _Node,
    target: _Node,
    props: Mapping[str, Any] | None = None,
  ) -> _Edge:
    kept = dict(props or {})
    cursor = self.db.execute(
      "INSERT INTO edges (label, src, dst, props) VALUES (?, ?, ?, ?)",
      (label, source.id, target.id, json.dumps(kept, separators=(",", ":"))),
    )
    return _Edge(cursor.lastrowid or 0, label, source.id, target.id, kept)

  def delete_node(self, node: _Node, *, detach: bool) -> None:
    if node.deleted:
      return
    attached = self.db.execute(
      "SELECT COUNT(*) FROM edges WHERE src = ? OR dst = ?", (node.id, node.id)
    ).fetchone()[0]
    if attached and not detach:
      raise GraphBackendError(
        "Cannot delete a node that still has relationships.", code="CONFLICT"
      )
    self.db.execute("DELETE FROM edges WHERE src = ? OR dst = ?", (node.id, node.id))
    self.db.execute("DELETE FROM large_values WHERE node = ?", (node.id,))
    self.db.execute("DELETE FROM nodes WHERE id = ?", (node.id,))
    node.deleted = True

  def delete_edge(self, edge: _Edge) -> None:
    if not edge.deleted:
      self.db.execute("DELETE FROM edges WHERE id = ?", (edge.id,))
      edge.deleted = True

  # Statements --------------------------------------------------------------------

  def statement(self, block: ast.StatementBlock) -> list[dict[str, JsonValue]]:
    rows: list[_Row] = [{}]
    parts = [
      block.statement,
      *(item.statement for item in block.list_next_statement or []),
    ]
    result: list[dict[str, JsonValue]] = []
    for part in parts:
      statements, returned = _part(part)
      for item in statements:
        rows = self.apply(item, rows)
      if returned is not None:
        result = self.result(returned, rows)
    return result

  def apply(self, statement: Any, rows: list[_Row]) -> list[_Row]:
    kind = type(statement).__name__
    if kind == "SimpleMatchStatement":
      return [
        found for row in rows for found in self.match(statement, row, optional=False)
      ]
    if kind == "OptionalMatchStatement":
      inner = statement.find_first(ast.SimpleMatchStatement)
      return [found for row in rows for found in self.match(inner, row, optional=True)]
    if kind == "InsertStatement":
      for row in rows:
        self.insert(statement, row)
      return rows
    if kind == "SetStatement":
      for row in rows:
        for item in statement.set_item_list.list_set_item:
          if type(item).__name__ != "SetPropertyItem":
            raise Unsupported(type(item).__name__)
          target = row.get(item.binding_variable_reference.binding_variable.name)
          name = item.property_name.identifier.name
          if isinstance(target, _Node):
            self.update(target, {name: self.eval(item.value_expression, row)})
          elif isinstance(target, _Edge):
            self.update_edge(target, {name: self.eval(item.value_expression, row)})
      return rows
    if kind == "DeleteStatement":
      detach = statement.mode is not None and statement.mode.name == "DETACH"
      for row in rows:
        for item in statement.delete_item_list.list_delete_item:
          target = self.eval_element(item, row)
          if isinstance(target, _Node):
            self.delete_node(target, detach=detach)
          elif isinstance(target, _Edge):
            self.delete_edge(target)
      return rows
    raise Unsupported(kind)

  # Matching ----------------------------------------------------------------------

  def match(self, statement: Any, row: _Row, *, optional: bool) -> list[_Row]:
    pattern = statement.graph_pattern_binding_table.graph_pattern
    if pattern.match_mode is not None or pattern.keep_clause is not None:
      raise Unsupported("match modes")
    where = pattern.graph_pattern_where_clause
    condition = where.search_condition if where is not None else None
    lookups = _identity_lookups(condition)
    paths = [
      path.path_pattern_expression
      for path in pattern.path_pattern_list.list_path_pattern
    ]
    declared = {name for path in paths for name in _declared(path)}
    found = [
      candidate
      for candidate in self._paths(paths, dict(row), lookups)
      if condition is None or self.eval(condition, candidate) is True
    ]
    if not found and optional:
      return [{**row, **{name: None for name in declared if name not in row}}]
    return found

  def _paths(
    self, paths: Sequence[Any], row: _Row, lookups: Mapping[str, Any]
  ) -> Iterator[_Row]:
    if not paths:
      yield row
      return
    for extended in self._path(list(paths[0].factors), row, lookups, None):
      yield from self._paths(paths[1:], extended, lookups)

  def _path(
    self,
    factors: list[Any],
    row: _Row,
    lookups: Mapping[str, Any],
    previous: _Node | None,
  ) -> Iterator[_Row]:
    if not factors:
      yield row
      return
    head = factors[0]
    kind = type(head).__name__
    if kind != "NodePattern":
      raise Unsupported(f"pattern element {kind}")
    name, label = _filler(head.element_pattern_filler)
    for node in self._nodes(name, label, row, lookups):
      bound = {**row, name: node} if name else row
      if len(factors) == 1:
        yield bound
        continue
      edge_pattern, rest = factors[1], factors[2:]
      edge_kind = type(edge_pattern).__name__
      if edge_kind not in ("FullEdgePointingRight", "FullEdgePointingLeft"):
        raise Unsupported(f"edge pattern {edge_kind}")
      edge_name, edge_label = _filler(edge_pattern.element_pattern_filler)
      if edge_label is None:
        raise Unsupported("edges without a label")
      outgoing = edge_kind == "FullEdgePointingRight"
      for edge in self.edges(node, edge_label, outgoing):
        target = self.node(edge.dst if outgoing else edge.src)
        if target.deleted:
          continue
        next_name, next_label = _filler(rest[0].element_pattern_filler)
        if next_label is not None and target.label != next_label:
          continue
        if next_name and next_name in bound and bound[next_name] is not target:
          continue
        if next_name is not None and next_name in lookups:
          try:
            expected = self.eval(lookups[next_name], bound)
          except _Unbound:
            expected = None
          if expected is not None and target.micro_id != str(expected):
            continue
        extended = dict(bound)
        if edge_name:
          extended[edge_name] = edge
        if next_name:
          extended[next_name] = target
        yield from self._path(rest[1:], extended, lookups, target)

  def _nodes(
    self, name: str | None, label: str | None, row: _Row, lookups: Mapping[str, Any]
  ) -> list[_Node]:
    if name and name in row:
      node = row[name]
      if not isinstance(node, _Node) or node.deleted:
        return []
      return [node] if label is None or node.label == label else []
    if label is None:
      raise Unsupported("node patterns without a label")
    if name is not None and name in lookups:
      try:
        identity = self.eval(lookups[name], row)
      except _Unbound:
        return self.by_label(label)
      return self.by_label(label, identity)
    return self.by_label(label)

  # Writes ------------------------------------------------------------------------

  def insert(self, statement: Any, row: _Row) -> None:
    for path in statement.insert_graph_pattern.list_insert_path_pattern:
      previous = self._insert_node(path.insert_node_pattern, row)
      for step in path.list_insert_edge_pattern_insert_node_pattern or []:
        edge, target = list(step.children())
        node = self._insert_node(target, row)
        if previous is None or node is None:
          previous = node
          continue
        name, label, edge_props = _insert_filler(edge, self, row)
        if label is None:
          raise Unsupported("inserting an edge without a label")
        pointing_right = type(edge).__name__ == "InsertEdgePointingRight"
        source, destination = (previous, node) if pointing_right else (node, previous)
        created = self.connect(label, source, destination, edge_props)
        if name:
          row[name] = created
        previous = node

  def _insert_node(self, pattern: Any, row: _Row) -> _Node | None:
    name, label, props = _insert_filler(pattern, self, row)
    if label is None:
      if name is None:
        raise Unsupported("anonymous node insertion without a label")
      existing = row.get(name)
      return existing if isinstance(existing, _Node) else None
    node = self.create(label, props)
    if name:
      row[name] = node
    return node

  # Results -----------------------------------------------------------------------

  def result(self, statement: Any, rows: list[_Row]) -> list[dict[str, JsonValue]]:
    inner = statement.primitive_result_statement
    returned = getattr(inner, "return_statement", None)
    if returned is None:
      raise Unsupported(type(inner).__name__)
    body = returned.return_statement_body.return_statement_body
    if body.set_quantifier is not None or body.group_by_clause is not None:
      raise Unsupported("DISTINCT or GROUP BY")
    page = getattr(inner, "order_by_and_page_statement", None)
    page = page.order_by_and_page_statement if page is not None else None
    if page is not None and page.order_by_clause is not None:
      for spec in reversed(
        page.order_by_clause.sort_specification_list.list_sort_specification
      ):
        descending = (
          spec.ordering_specification is not None
          and spec.ordering_specification.ordering_specification.name == "DESC"
        )
        rows.sort(
          key=lambda row, spec=spec: _sort_key(self.eval(spec.sort_key, row)),
          reverse=descending,
        )
    offset = (self._count(page.offset_clause) or 0) if page is not None else 0
    limit = self._count(page.limit_clause) if page is not None else None
    selected = rows[offset:] if limit is None else rows[offset : offset + limit]
    items = body.return_item_list.list_return_item
    return [
      {
        item.return_item_alias.identifier.name: self.eval(
          item.aggregating_value_expression, row
        )
        for item in items
      }
      for row in selected
    ]

  def _count(self, clause: Any) -> Any:
    if clause is None:
      return None
    value = self.eval(clause.non_negative_integer_specification, {})
    return int(value) if value is not None else None

  # Expressions -------------------------------------------------------------------

  def eval_element(self, node: Any, row: _Row) -> _Node | _Edge | None:
    reference = (
      node
      if type(node).__name__ == "BindingVariableReference"
      else node.find_first(ast.BindingVariableReference)
    )
    if reference is None:
      raise Unsupported("deleting an expression")
    return row.get(reference.binding_variable.name)

  def eval(self, node: Any, row: _Row) -> Any:
    kind = type(node).__name__
    method = getattr(self, f"_eval_{kind.lstrip('_')}", None)
    if method is not None:
      return method(node, row)
    children = list(node.children())
    if len(children) == 1:
      return self.eval(children[0], row)
    raise Unsupported(f"the expression {kind}")

  def _eval_BooleanValueExpression(self, node: Any, row: _Row) -> Any:
    value = self.eval(node.boolean_term, row)
    for step in node.ops or []:
      other = self.eval(step.boolean_term, row)
      if step.operator.name == "OR":
        value = (
          True
          if value is True or other is True
          else None
          if None in (value, other)
          else False
        )
      else:
        value = None if None in (value, other) else value != other
    return value

  def _eval_BooleanTerm(self, node: Any, row: _Row) -> Any:
    result: Any = True
    for factor in node.list_boolean_factor:
      value = self.eval(factor, row)
      if value is False:
        return False
      if value is None:
        result = None
    return result

  def _eval_BooleanFactor(self, node: Any, row: _Row) -> Any:
    value = self.eval(node.boolean_test, row)
    if node.not_:
      return None if value is None else not value
    return value

  def _eval_BooleanTest(self, node: Any, row: _Row) -> Any:
    if node.truth_value is not None:
      raise Unsupported("IS TRUE/FALSE/UNKNOWN")
    return self.eval(node.boolean_primary, row)

  def _eval_ComparisonPredicate(self, node: Any, row: _Row) -> Any:
    left = self.eval(node.comparison_predicand, row)
    part = node.comparison_predicate_part_2
    right = self.eval(part.comparison_predicand, row)
    if left is None or right is None:
      return None
    operator = part.comp_op.name
    try:
      if operator == "EQUALS":
        return _equal(left, right)
      if operator == "NOT_EQUALS":
        return not _equal(left, right)
      if operator == "LESS_THAN":
        return left < right
      if operator == "GREATER_THAN":
        return left > right
      if operator == "LESS_THAN_OR_EQUALS":
        return left <= right
      return left >= right
    except TypeError:
      return None

  def _eval_NullPredicate(self, node: Any, row: _Row) -> Any:
    is_null = self.eval(node.value_expression_primary, row) is None
    return not is_null if node.null_predicate_part_2.not_ else is_null

  def _eval_ArithmeticValueExpression(self, node: Any, row: _Row) -> Any:
    value = self.eval(node.base, row)
    for step in node.steps or []:
      other = self.eval(step.term, row)
      plus = step.sign.name == "PLUS_SIGN"
      if (
        isinstance(other, dict) and plus and (value is None or isinstance(value, dict))
      ):
        # A map plus a map: the entries of the second set or replace those of the first
        # (a missing map counts as empty), so one key changes atomically.
        value = {**(value or {}), **other}  # pyright: ignore[reportUnknownVariableType]
        continue
      if isinstance(value, dict) and not plus and isinstance(other, str | list):
        # A map minus a key (or a list of keys): those entries are gone.
        gone = {other} if isinstance(other, str) else set(other)  # pyright: ignore[reportUnknownArgumentType]
        value = {k: v for k, v in value.items() if k not in gone}  # pyright: ignore[reportUnknownVariableType]
        continue
      if value is None or other is None:
        return None
      left: Any = value
      value = left + other if plus else left - other
    return value

  def _eval_ArithmeticTerm(self, node: Any, row: _Row) -> Any:
    value = self.eval(node.base, row)
    for step in node.steps or []:
      other = self.eval(step.factor, row)
      if value is None or other is None:
        return None
      value = value * other if step.operator.name == "MULTIPLY" else value / other
    return value

  def _eval_ArithmeticFactor(self, node: Any, row: _Row) -> Any:
    value = self.eval(node.arithmetic_primary, row)
    if node.sign is not None and node.sign.name == "MINUS_SIGN" and value is not None:
      return -value
    return value

  def _eval_CharacterStringValueExpression(self, node: Any, row: _Row) -> Any:
    values = [
      self.eval(item, row) for item in node.list_character_string_value_expression
    ]
    if len(values) == 1:
      return values[0]
    return None if None in values else "".join(str(value) for value in values)

  def _eval_GeneralParameterReference(self, node: Any, row: _Row) -> Any:
    name = node.parameter_name.name
    if name not in self.params:
      raise GraphBackendError(f"Missing parameter ${name}.", code="INVALID")
    return self.params[name]

  def _eval_PropertyReference(self, node: Any, row: _Row) -> Any:
    target: Any = self.eval(node.property_source, row)
    for name in node.property_name:
      key = name.identifier.name
      if isinstance(target, _Node):
        target = self.get(target, key)
      elif isinstance(target, _Edge):
        target = str(target.id) if key == "_micro_id" else target.props.get(key)
      elif isinstance(target, dict):
        target = target.get(key)  # pyright: ignore[reportUnknownMemberType]
      else:
        return None
    return target

  def _eval_BindingVariableReference(self, node: Any, row: _Row) -> Any:
    name = node.binding_variable.name
    if name not in row:
      raise _Unbound(name)
    return row[name]

  def _eval_BooleanLiteral(self, node: Any, row: _Row) -> Any:
    return node.value

  def _eval_UnsignedNumericLiteral(self, node: Any, row: _Row) -> Any:
    return node.value

  def _eval_UnsignedInteger(self, node: Any, row: _Row) -> Any:
    return node.value

  def _eval_CharacterStringLiteral(self, node: Any, row: _Row) -> Any:
    return node.value

  def _eval_NullLiteral(self, node: Any, row: _Row) -> Any:
    return None


class _Unbound(LookupError):
  pass


def _part(part: Any) -> tuple[list[Any], Any]:
  """A linear statement's clauses and its result statement (or None)."""
  kind = type(part).__name__
  if kind == "AmbientLinearDataModifyingStatementBody":
    body = part.simple_linear_data_accessing_statement
    statements = list(body.list_simple_data_accessing_statement or []) if body else []
    return statements, part.primitive_result_statement
  if kind == "CompositeQueryExpression":
    if part.query_conjunction_elements:
      raise Unsupported("UNION/EXCEPT/INTERSECT")
    return _part(part.left_composite_query_primary)
  if kind == "AmbientLinearQueryStatement":
    return _part(part.ambient_linear_query_statement)
  if kind == "_SimpleLinearQueryStatementPrimitiveResultStatement":
    body = part.simple_linear_query_statement
    statements = list(body.list_simple_query_statement or []) if body else []
    return statements, part.primitive_result_statement
  if kind == "PrimitiveResultStatement":
    return [], part
  raise Unsupported(kind)


def _equal(left: Any, right: Any) -> bool:
  if isinstance(left, bool) != isinstance(right, bool):
    return False
  return left == right


def _sort_key(value: Any) -> tuple[int, Any]:
  if value is None:
    return (2, "")
  if isinstance(value, bool | int | float):
    return (0, value)
  return (1, json.dumps(value, sort_keys=True) if not isinstance(value, str) else value)


def _filler(filler: Any) -> tuple[str | None, str | None]:
  declaration = filler.element_variable_declaration
  name = declaration.element_variable.name if declaration is not None else None
  label = None
  expression = filler.is_label_expression
  if expression is not None:
    terms = expression.label_expression.label_terms
    if len(terms) != 1 or len(terms[0].label_factors) != 1:
      raise Unsupported("label expressions")
    factor = terms[0].label_factors[0]
    if type(factor).__name__ != "LabelName":
      raise Unsupported("label expressions")
    label = factor.identifier.name
  if getattr(filler, "element_pattern_predicate", None) is not None:
    raise Unsupported("inline pattern predicates")
  return name, label


def _declared(path: Any) -> list[str]:
  names: list[str] = []
  for factor in path.factors:
    name, _ = _filler(factor.element_pattern_filler)
    if name:
      names.append(name)
  return names


def _insert_filler(
  pattern: Any, run: _Run, row: _Row
) -> tuple[str | None, str | None, dict[str, Any]]:
  declaration = pattern.find_first(ast.ElementVariableDeclaration)
  name = declaration.element_variable.name if declaration is not None else None
  labels = [item.identifier.name for item in pattern.find_all(ast.LabelName)]
  if len(labels) > 1:
    raise Unsupported("multiple labels")
  props = {
    pair.property_name.identifier.name: run.eval(pair.value_expression, row)
    for pair in pattern.find_all(ast.PropertyKeyValuePair)
  }
  return name, labels[0] if labels else None, props


def _identity_lookups(condition: Any) -> dict[str, Any]:
  """`v._micro_id = expr` conjuncts, used as index lookups while matching."""
  lookups: dict[str, Any] = {}
  if (
    condition is None
    or type(condition).__name__ != "BooleanValueExpression"
    or condition.ops
  ):
    return lookups
  for factor in condition.boolean_term.list_boolean_factor:
    test: Any = factor.boolean_test
    if test is None or factor.not_ or test.truth_value is not None:
      continue
    primary: Any = test.boolean_primary
    if type(primary).__name__ != "ComparisonPredicate":
      continue
    part = primary.comparison_predicate_part_2
    if part.comp_op.name != "EQUALS":
      continue
    for side, other in (
      (primary.comparison_predicand, part.comparison_predicand),
      (part.comparison_predicand, primary.comparison_predicand),
    ):
      reference = (
        side.find_first(ast.PropertyReference)
        if type(side).__name__ != "PropertyReference"
        else side
      )
      if (
        reference is not None
        and _only_child_chain(side, reference)
        and len(reference.property_name) == 1
        and reference.property_name[0].identifier.name == "_micro_id"
        and type(reference.property_source).__name__ == "BindingVariableReference"
      ):
        lookups[reference.property_source.binding_variable.name] = other
        break
  return lookups


def _only_child_chain(node: Any, target: Any) -> bool:
  while node is not target:
    children = list(node.children())
    if len(children) != 1:
      return False
    node = children[0]
  return True


class SQLiteGraph:
  """`GraphExecutor` storing the graph in one SQLite file (see module docs)."""

  def __init__(self, path: str | Path = ".micro/store.db") -> None:
    self.path = Path(path)
    self._worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix="micro-sqlite")
    self._db: sqlite3.Connection | None = None
    self._gql = Dialect.get_or_raise("fullgql")
    self._parsed: dict[str, ast.StatementBlock] = {}

  async def start(self) -> None:
    """Open (creating) the SQLite file."""
    await self._call(self._open)

  async def close(self) -> None:
    """Close the database."""
    if self._db is not None:
      await self._call(self._db.close)
      self._db = None
    self._worker.shutdown(wait=True)

  async def execute(self, batch: GraphBatch) -> GraphBatchResult:
    """Run a batch of statements in one transaction."""
    return await self._call(self._execute, batch)

  async def apply_layout(self, layout: GraphLayout) -> None:
    """Record the layout; the graph is schemaless, so nothing physical changes."""
    definition = json.dumps(
      [
        [entity.name, entity.label, [list(key) for key in entity.keys]]
        for entity in layout.entities
      ]
    )

    def record() -> None:
      db = self._connection()
      with db:
        db.execute(
          "INSERT INTO layouts (revision, definition) VALUES (?, ?) "
          "ON CONFLICT (revision) DO UPDATE SET definition = excluded.definition",
          (layout.revision, definition),
        )

    await self._call(record)

  async def _call(self, function: Any, *args: Any) -> Any:
    return await asyncio.get_running_loop().run_in_executor(
      self._worker, function, *args
    )

  def _open(self) -> None:
    self.path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(self.path, isolation_level=None, check_same_thread=False)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=NORMAL")
    db.execute("PRAGMA foreign_keys=ON")
    # Wait for other store processes' writes instead of failing (SQLite's lock).
    db.execute("PRAGMA busy_timeout=2147483647")
    db.executescript(_SCHEMA)
    if not any(
      column[1] == "props" for column in db.execute("PRAGMA table_info(edges)")
    ):
      # A store made before edges had properties: add the column; old edges get {}.
      db.execute("ALTER TABLE edges ADD COLUMN props TEXT NOT NULL DEFAULT '{}'")
    self._db = db

  def _connection(self) -> sqlite3.Connection:
    if self._db is None:
      raise GraphBackendError(
        "The SQLite graph is not open.", code="UNAVAILABLE", retryable=True
      )
    return self._db

  def _block(self, statement: GraphStatement) -> ast.StatementBlock:
    block = self._parsed.get(statement.text)
    if block is None:
      trees = self._gql.parse(statement.text)
      found = trees[0].find_first(ast.StatementBlock) if len(trees) == 1 else None
      if found is None:
        raise Unsupported("this statement shape")
      block = self._parsed[statement.text] = found
    return block

  def _execute(self, batch: GraphBatch) -> GraphBatchResult:
    db = self._connection()
    writes = any(
      keyword in statement.text
      for statement in batch.statements
      for keyword in ("INSERT", "SET ", "DELETE")
    )
    try:
      db.execute("BEGIN IMMEDIATE" if writes else "BEGIN")
      try:
        results = []
        for statement in batch.statements:
          run = _Run(db, statement.parameters)
          rows = run.statement(self._block(statement))
          results.append(
            GraphResult(
              tuple(
                {column: row.get(column) for column in statement.columns}
                for row in rows
              )
            )
          )
      except BaseException:
        db.execute("ROLLBACK")
        raise
      db.execute("COMMIT")
      return GraphBatchResult(tuple(results))
    except sqlite3.IntegrityError as exc:
      raise GraphBackendError(
        "The graph operation conflicts with existing data.", code="CONFLICT"
      ) from exc
    except sqlite3.OperationalError as exc:
      raise GraphBackendError(
        f"The graph backend is unavailable: {exc}", code="UNAVAILABLE", retryable=True
      ) from exc


__all__ = ("LARGE_VALUE", "SQLiteGraph")
