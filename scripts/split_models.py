"""Split one generated model module into a lazily imported package.

Every group of mutually referencing definitions (a strongly connected
component of the reference graph) becomes one small module; the package
`__init__` imports a name's module only when the name is first used.
Type checkers see every name through `TYPE_CHECKING` imports.

    python scripts/split_models.py gateway.py src/micro/discord/models/gateway \\
      --package micro.discord.models.gateway
"""

import argparse
import ast
import re
import shutil
from pathlib import Path

HEADER = "# Generated from Discord's API specification. Do not edit directly.\n"


def _references(node: ast.AST, names: set[str]) -> set[str]:
  found: set[str] = set()
  for child in ast.walk(node):
    if isinstance(child, ast.Name) and child.id in names:
      found.add(child.id)
    elif isinstance(child, ast.Constant) and isinstance(child.value, str):
      try:
        expression = ast.parse(child.value, mode="eval")
      except SyntaxError:
        continue
      found |= {
        item.id
        for item in ast.walk(expression)
        if isinstance(item, ast.Name) and item.id in names
      }
  return found


def _components(order: list[str], graph: dict[str, set[str]]) -> list[list[str]]:
  """Tarjan's strongly connected components, iteratively."""
  index: dict[str, int] = {}
  low: dict[str, int] = {}
  stack: list[str] = []
  on_stack: set[str] = set()
  result: list[list[str]] = []
  counter = 0
  for root in order:
    if root in index:
      continue
    work = [(root, iter(sorted(graph[root])))]
    index[root] = low[root] = counter
    counter += 1
    stack.append(root)
    on_stack.add(root)
    while work:
      node, children = work[-1]
      advanced = False
      for child in children:
        if child not in index:
          index[child] = low[child] = counter
          counter += 1
          stack.append(child)
          on_stack.add(child)
          work.append((child, iter(sorted(graph[child]))))
          advanced = True
          break
        if child in on_stack:
          low[node] = min(low[node], index[child])
      if advanced:
        continue
      work.pop()
      if work:
        parent = work[-1][0]
        low[parent] = min(low[parent], low[node])
      if low[node] == index[node]:
        component: list[str] = []
        while True:
          item = stack.pop()
          on_stack.discard(item)
          component.append(item)
          if item == node:
            break
        result.append(component)
  return result


def _module_name(name: str, used: set[str]) -> str:
  snake = re.sub(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", "_", name).lower()
  base = "_" + snake
  candidate, suffix = base, 2
  while candidate in used:  # Case-insensitive filesystems: keep names unique.
    candidate, suffix = f"{base}_{suffix}", suffix + 1
  used.add(candidate)
  return candidate


def split(source: Path, target: Path, package: str, rewrites: dict[str, str]) -> int:
  text = source.read_text()
  tree = ast.parse(text)
  imports: list[str] = []
  definitions: dict[str, ast.stmt] = {}
  order: list[str] = []
  rebuilds: dict[str, list[str]] = {}
  for node in tree.body:
    if isinstance(node, ast.Import | ast.ImportFrom):
      line = ast.get_source_segment(text, node) or ast.unparse(node)
      imports.append(rewrites.get(line, line))
    elif isinstance(node, ast.ClassDef):
      definitions[node.name] = node
      order.append(node.name)
    elif isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
      name = node.targets[0].id
      if name == "__all__":
        continue
      definitions[name] = node
      order.append(name)
    elif (
      isinstance(node, ast.Expr)
      and isinstance(node.value, ast.Call)
      and isinstance(node.value.func, ast.Attribute)
      and isinstance(node.value.func.value, ast.Name)
    ):
      owner = node.value.func.value.id
      rebuilds.setdefault(owner, []).append(ast.get_source_segment(text, node) or "")
    elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
      continue  # Module docstring.
    else:
      raise TypeError(f"Unsupported top-level statement: {ast.unparse(node)[:80]}")

  names = set(definitions)
  graph = {name: _references(definitions[name], names) - {name} for name in order}
  position = {name: index for index, name in enumerate(order)}
  components = _components(order, graph)
  used: set[str] = set()
  module_of: dict[str, str] = {}
  modules: list[tuple[str, list[str]]] = []
  for component in sorted(
    components, key=lambda items: min(position[i] for i in items)
  ):
    members = sorted(component, key=position.__getitem__)
    module = _module_name(members[0], used)
    modules.append((module, members))
    for member in members:
      module_of[member] = module

  if target.exists():
    shutil.rmtree(target)
  target.mkdir(parents=True)
  for module, members in modules:
    external = sorted(
      {dep for member in members for dep in graph[member] if module_of[dep] != module},
      key=position.__getitem__,
    )
    lines = [HEADER, *imports, ""]
    lines += [
      f"from .{module_of[dependency]} import {dependency}" for dependency in external
    ]
    for member in members:
      lines += ["", "", ast.get_source_segment(text, definitions[member]) or ""]
    rebuild = [call for member in members for call in rebuilds.get(member, [])]
    if rebuild:
      lines += ["", "", *rebuild]
    (target / f"{module}.py").write_text("\n".join(lines).rstrip() + "\n")

  index = [
    HEADER.rstrip(),
    '"""Lazily imported models: each name loads only its own module."""',
    "",
    "from importlib import import_module",
    "from typing import TYPE_CHECKING, Any",
    "",
    "if TYPE_CHECKING:",
  ]
  index += [f"  from .{module_of[name]} import {name} as {name}" for name in order]
  index += ["", "_MODULES: dict[str, str] = {"]
  index += [f'  "{name}": "{module_of[name]}",' for name in order]
  index += [
    "}",
    "",
    "",
    "def __getattr__(name: str) -> Any:",
    "  try:",
    "    module = _MODULES[name]",
    "  except KeyError:",
    f'    raise AttributeError(f"module {package!r} has no attribute {{name!r}}") from None',
    '  value = getattr(import_module(f".{module}", __name__), name)',
    "  globals()[name] = value",
    "  return value",
    "",
    "",
    "def __dir__() -> list[str]:",
    "  return sorted(_MODULES)",
    "",
    "",
    "__all__ = (",
  ]
  index += [f'  "{name}",' for name in sorted(order)]
  index += [")", ""]
  (target / "__init__.py").write_text("\n".join(index))
  return len(modules)


def main() -> None:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("source", type=Path)
  parser.add_argument("target", type=Path)
  parser.add_argument("--package", required=True)
  parser.add_argument(
    "--rewrite",
    action="append",
    default=[],
    help="replace an import line: 'OLD=>NEW'",
  )
  args = parser.parse_args()
  rewrites = dict(item.split("=>", 1) for item in args.rewrite)
  count = split(args.source, args.target, args.package, rewrites)
  print(f"Split {args.source.name} into {count} modules under {args.target}")


if __name__ == "__main__":
  main()
