"""Generate src/micro/discord/_actions.py: every action of a ref, on the object itself.

    uv run python scripts/gen_actions.py     # after scripts/gen_api.py

`message.reply(...)`, `member.ban(...)`, `guild.fetch_roles()`: one method per method of the
matching ref (`MessageRef`, `MemberRef`, ...), with the same signature and docstring, read
from the generated `refs.py`, so a new operation shows up on the object by regenerating.
A name the object already has (`guild.roles` is the cached list) becomes `fetch_<name>`,
and `get` is `fetch`.
"""

import ast
import importlib
import inspect
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REFS = ROOT / "src/micro/discord/refs.py"
EXTRAS = ROOT / "src/micro/discord/_refs.py"
OUT = ROOT / "src/micro/discord/_actions.py"

OBJECTS: dict[str, tuple[str, str, str, frozenset[str] | None]] = {
  # object: (ref class, how to reach the ref, the full model name, only these methods)
  "Message": (
    "MessageRef",
    "self.context.api.message(self.channel_id, self.id)",
    "MessageResponse",
    None,
  ),
  "Member": (
    "MemberRef",
    "self.context.api.member(self.guild_id, self.id)",
    "GuildMemberResponse",
    None,
  ),
  "User": ("UserRef", "self.context.api.user(self.id)", "UserResponse", None),
  "Channel": (
    "ChannelRef",
    "self.context.api.channel(self.id)",
    "GuildChannelResponse",
    None,
  ),
  "Guild": ("GuildRef", "self.context.api.guild(self.id)", "GuildResponse", None),
  "Role": (
    "RoleRef",
    "self.context.api.role(self.guild_id, self.id)",
    "GuildRoleResponse",
    None,
  ),
}
ALSO: dict[str, tuple[str, str, frozenset[str]]] = {
  "Member": ("UserRef", "self.context.api.user(self.id)", frozenset({"send", "dm"})),
}
NEEDS: dict[str, tuple[str, ...]] = {
  "Message": ("id: str", "channel_id: str"),
  "Member": ("id: str", "guild_id: str"),
  "User": ("id: str",),
  "Channel": ("id: str",),
  "Guild": ("id: str",),
  "Role": ("id: str", "guild_id: str | None"),
}


def methods_of(
  tree: ast.Module, name: str, extras: dict[str, ast.ClassDef]
) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
  classes = {c.name: c for c in tree.body if isinstance(c, ast.ClassDef)}
  found: list[ast.FunctionDef | ast.AsyncFunctionDef] = []
  seen: set[str] = set()
  stack = [classes[name]]
  while stack:
    cls = stack.pop(0)
    for node in cls.body:
      if (
        isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        and not node.name.startswith("_")
        and node.name not in seen
      ):
        seen.add(node.name)
        found.append(node)
    for base in cls.bases:
      if isinstance(base, ast.Name) and base.id in extras:
        stack.append(extras[base.id])
  return found


def taken(view: str) -> set[str]:
  """Names the object has already: its fields, properties and methods, and Discord's."""
  module = importlib.import_module("micro.discord.objects")
  cls = getattr(module, view)
  names = set(dir(cls)) | set(getattr(cls, "model_fields", {}))
  models = importlib.import_module("micro.discord.models.http")
  full = getattr(cls, "_full", None)
  model = getattr(models, full, None) if isinstance(full, str) else None
  for candidate in (model,):
    fields = getattr(candidate, "model_fields", None)
    if fields:
      names |= set(fields)
  # the mixin's own previous output is not "already there"
  for attr in list(names):
    if inspect.isfunction(getattr(cls, attr, None)) and getattr(
      getattr(cls, attr), "__module__", ""
    ).endswith("_actions"):
      names.discard(attr)
  return names


def forward(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
  args = node.args
  parts: list[str] = []
  for a in [*args.posonlyargs, *args.args][1:]:
    parts.append(a.arg)
  if args.vararg:
    parts.append("*" + args.vararg.arg)
  for a in args.kwonlyargs:
    parts.append(f"{a.arg}={a.arg}")
  if args.kwarg:
    parts.append("**" + args.kwarg.arg)
  return ", ".join(parts)


def render_method(
  node: ast.FunctionDef | ast.AsyncFunctionDef, public: str, ref: str, view: str
) -> str:
  signature = ast.unparse(node.args)
  returns = f" -> {ast.unparse(node.returns)}" if node.returns else ""
  keyword = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
  doc = ast.get_docstring(node) or ""
  call = f"{ref}.{node.name}({forward(node)})"
  body = (
    f"return await {call}"
    if isinstance(node, ast.AsyncFunctionDef)
    else f"return {call}"
  )
  summary = (
    doc.splitlines()[0] if doc else f"`{node.name}` of this {view.lower()}'s ref."
  )
  return (
    f"  {keyword} {public}({signature}){returns}:\n"
    f'    """{summary}"""\n'
    f"    {body}\n"
  )


def generate() -> str:
  tree = ast.parse(REFS.read_text())
  extra_tree = ast.parse(EXTRAS.read_text())
  extras = {c.name: c for c in extra_tree.body if isinstance(c, ast.ClassDef)}
  header = REFS.read_text().split("\n@dataclass")[0]
  imports = "\n".join(
    line
    for line in header.splitlines()
    if line.startswith(("from ", "import ")) and "_refs" not in line
  )
  ref_names = sorted(
    c.name for c in tree.body if isinstance(c, ast.ClassDef) and c.name.endswith("Ref")
  )
  imports += "\nfrom micro.discord.refs import (" + ", ".join(ref_names) + ")"
  out = [
    "# Generated by scripts/gen_actions.py. Do not edit.",
    '"""Every action of a ref, on the object itself (`message.reply`, `member.ban`, ...)."""',
    "",
    imports,
    "",
    "",
  ]
  names: dict[str, list[str]] = {}
  for view, (ref_class, reach, _model, _only) in OBJECTS.items():
    out += [
      "",
      f"class {view}Actions:",
      f'  """The actions of a {view.lower()}: what its ref can do, on the object."""',
      "",
    ]
    checks = [
      f'    if me.{n.split(":")[0]} is None:\n'
      f'      raise RuntimeError("This {view} does not know its {n.split(":")[0]}, so it cannot act.")'
      for n in NEEDS[view]
      if n.endswith("| None")
    ]
    out += [
      f"  def _ref(self) -> {ref_class}:",
      "    me: Any = self",
      *checks,
      f"    return {reach.replace('self.', 'me.')}",
      "",
    ]
    already = taken(view)
    done: list[str] = []
    for node in methods_of(tree, ref_class, extras):
      public = "fetch" if node.name == "get" else node.name
      if public in already or public in done:
        public = f"fetch_{public}"
      done.append(public)
      out.append(render_method(node, public, "self._ref()", view))
    if view in ALSO:
      other, reach2, only = ALSO[view]
      out += [
        f"  def _user_ref(self) -> {other}:",
        "    me: Any = self",
        f"    return {reach2.replace('self.', 'me.')}",
        "",
      ]
      for node in methods_of(tree, other, extras):
        if node.name in only and node.name not in done:
          done.append(node.name)
          out.append(render_method(node, node.name, "self._user_ref()", view))
    names[view] = done
  return "\n".join(out) + "\n"


if __name__ == "__main__":
  if not OUT.exists():
    OUT.write_text("")
  text = generate()
  OUT.write_text(text)
  print(f"wrote {OUT.name}")
