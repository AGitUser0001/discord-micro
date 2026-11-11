"""`micro docs`: render the bundled ReST docs to HTML and open them.

The docs ship inside the wheel, so they always match the installed Micro. No
build step and nothing written to disk: pages are rendered with docutils in
memory and served on 127.0.0.1 only while the command runs.
"""

import asyncio
import html
import inspect
import io
import json
import re
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib import resources
from importlib.metadata import PackageNotFoundError, version
from typing import Any, ClassVar

from docutils import nodes
from docutils.core import publish_parts
from docutils.parsers.rst import Directive, directives, roles
from docutils.parsers.rst.directives.body import CodeBlock

from . import _docs_api

_STYLE = """
:root { color-scheme: light dark; --fg: #1f2328; --muted: #59636e; --bg: #fff;
  --side: #f6f8fa; --line: #d1d9e0; --code: #f6f8fa; --link: #0969da; }
@media (prefers-color-scheme: dark) { :root { --fg: #e6edf3; --muted: #9198a1;
  --bg: #0d1117; --side: #151b23; --line: #3d444d; --code: #151b23; --link: #4493f8; } }
* { box-sizing: border-box; }
body { margin: 0; font: 16px/1.6 system-ui, -apple-system, Segoe UI, sans-serif;
  color: var(--fg); background: var(--bg); display: flex; min-height: 100vh; }
nav { width: 15rem; flex: none; padding: 1.5rem 1rem; background: var(--side);
  border-right: 1px solid var(--line); position: sticky; top: 0; height: 100vh; overflow: auto; }
nav .brand { font-weight: 700; font-size: 1.2rem; display: block; margin-bottom: .2rem; }
nav .version { color: var(--muted); font-size: .85rem; margin-bottom: 1rem; display: block; }
nav a { display: block; padding: .2rem .5rem; border-radius: 6px; color: var(--fg); text-decoration: none; }
nav a:hover { background: var(--line); }
nav .group { display: block; margin: 1rem 0 .2rem; padding: 0 .5rem; color: var(--muted);
  font-size: .75rem; text-transform: uppercase; letter-spacing: .05em; }
nav a.current { background: var(--line); font-weight: 600; }
main { flex: 1; min-width: 0; max-width: 52rem; padding: 2rem 2.5rem 4rem; }
a { color: var(--link); }
h1, h2, h3 { line-height: 1.25; } h1 { font-size: 2rem; margin-top: 0; }
h2 { border-bottom: 1px solid var(--line); padding-bottom: .3rem; margin-top: 2rem; }
pre, code, tt { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: .88em; }
pre { background: var(--code); border: 1px solid var(--line); border-radius: 6px;
  padding: .8rem 1rem; overflow: auto; line-height: 1.45; }
code, tt.literal, span.literal { background: var(--code); padding: .1em .35em;
  border-radius: 4px; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: .88em; }
li > p { margin: .15rem 0; }
pre code { background: none; padding: 0; }
table { border-collapse: collapse; margin: 1rem 0; display: block; overflow: auto; }
th, td { border: 1px solid var(--line); padding: .35rem .7rem; text-align: left; vertical-align: top; }
nav input { width: 100%; padding: .35rem .5rem; margin: .5rem 0; border: 1px solid var(--line);
  border-radius: 6px; background: var(--bg); color: var(--fg); font: inherit; }
nav details { margin: 0; } nav summary { cursor: pointer; padding: .2rem .5rem; border-radius: 6px; }
nav summary a { display: inline; padding: 0; } nav summary:hover { background: var(--line); }
nav .sub a { padding: .05rem .5rem .05rem 1.4rem; font-size: .85rem; color: var(--muted); }
#results { margin: 0 0 .5rem; } #results a { padding: .25rem .5rem; }
#results small { display: block; color: var(--muted); font-size: .75rem; }
@media (max-width: 760px) { body { display: block; } nav { width: auto; height: auto;
  position: static; border-right: 0; border-bottom: 1px solid var(--line); }
  main { padding: 1.5rem 1rem 3rem; } }
"""

_PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · Micro</title><style>{style}</style></head>
<body><nav><a class="brand" href="index.html">Micro</a><span class="version">{version}</span>
<input id="q" type="search" placeholder="Search the manual   ( / )" autocomplete="off">
<div id="results"></div>{links}</nav><main>{body}</main><script>{script}</script></body></html>
"""

_TITLES: dict[str, str] = {}

_SCRIPT = """
const q = document.getElementById('q'), out = document.getElementById('results');
let index = null;
async function load() { return index ??= await (await fetch('search.json')).json(); }
function rank(e, t) {
  const n = e.n.toLowerCase(), f = e.f.toLowerCase();
  if (n === t) return 0; if (n.startsWith(t)) return 1; if (n.includes(t)) return 2;
  if (f.includes(t)) return 3; if (e.s.toLowerCase().includes(t)) return 4; return 9;
}
q.addEventListener('input', async () => {
  const t = q.value.trim().toLowerCase(); out.textContent = ''; if (!t) return;
  const hits = (await load()).map(e => [rank(e, t), e]).filter(x => x[0] < 9)
    .sort((a, b) => a[0] - b[0] || a[1].n.length - b[1].n.length).slice(0, 30);
  for (const [, e] of hits) {
    const a = document.createElement('a'); a.href = e.u; a.textContent = e.n + ' ';
    const k = document.createElement('small'); k.textContent = e.k + ' · ' + e.f + (e.s ? ' — ' + e.s : '');
    a.append(k); out.append(a);
  }
});
q.addEventListener('keydown', e => {
  if (e.key === 'Enter') { const a = out.querySelector('a'); if (a) location = a.href; }
  if (e.key === 'Escape') { q.value = ''; out.textContent = ''; q.blur(); }
});
document.addEventListener('keydown', e => {
  if (e.key === '/' && document.activeElement !== q) { e.preventDefault(); q.focus(); }
});
"""

_MANUAL = {
  "micro.discord.interactions": "Interactions",
  "micro.discord.ui": "UI kit",
  "micro.discord.objects": "Objects",
  "micro.discord.enums": "Enumerations",
  "micro.discord.asset": "Assets",
  "micro.discord.colour": "Colours",
  "micro.discord.permissions": "Permissions",
  "micro.discord.state": "State",
  "micro.discord.refs": "Refs",
  "micro.discord.api": "API operations",
  "micro.discord.http_service": "HTTP worker and client",
  "micro.discord.filters": "Filters",
  "micro.discord.text": "Text helpers",
  "micro.discord.invite": "Invites",
  "micro.service": "Services",
  "micro.runtime": "Runtime",
  "micro.coordination": "Coordination",
  "micro.config": "Config",
  "micro.scheduler": "Scheduler",
  "micro.gateway": "Gateway",
  "micro.store": "Store",
  "micro.middleware": "Middleware",
  "micro.errors": "Errors",
  "micro.log": "Logging",
  "micro.result": "Results",
}
"""The manual: one page per module, generated from the code and its docstrings."""


def _manual_page(module: str) -> str:
  return "manual-" + module.removeprefix("micro.").replace(".", "-")


def _manual_sources() -> dict[str, str]:
  """`{page: ReST}` for the manual, written from what each module exports."""
  import importlib

  pages: dict[str, str] = {}
  for module, title in _MANUAL.items():
    intro = (importlib.import_module(module).__doc__ or "").strip().split("\n\n")[0]
    names = "\n".join(f"   {module}.{n}" for n in _docs_api.public_names(module))
    pages[_manual_page(module)] = (
      f"{title}\n{'=' * len(title)}\n\n``{module}``\n\n{intro}\n\n.. api::\n{names}\n"
    )
  return pages


def _source() -> Any:
  return resources.files("micro") / "docs"


def _title(name: str) -> str:
  if name.startswith("manual-"):
    return next(t for m, t in _MANUAL.items() if _manual_page(m) == name)
  if name not in _TITLES:
    text = (_source() / f"{name}.rst").read_text()
    lines = [line for line in text.splitlines() if line.strip()]
    _TITLES[name] = lines[0].strip() if lines else name
  return _TITLES[name]


def _doc_role(
  name: str,
  rawtext: str,
  text: str,
  lineno: int,
  inliner: Any,
  options: Any = None,
  content: Any = None,
) -> tuple[list[nodes.Node], list[nodes.system_message]]:
  match = re.fullmatch(r"(.*?)\s*<([^>]+)>", text)
  label, target = (match.group(1), match.group(2)) if match else (None, text)
  page, _, fragment = target.partition("#")
  if page not in _all_pages():
    message = inliner.reporter.warning(f"No page {page!r} for :doc:", line=lineno)
    return [nodes.literal(rawtext, label or page)], [message]
  uri = f"{page}.html" + (f"#{fragment}" if fragment else "")
  return [nodes.reference(rawtext, label or _title(page), refuri=uri)], []


def _all_pages() -> set[str]:
  return {
    entry.name.removesuffix(".rst")
    for entry in _source().iterdir()
    if entry.name.endswith(".rst")
  }


class _TocTree(Directive):
  has_content = True
  option_spec: ClassVar[dict[str, Any]] = {  # pyright: ignore[reportIncompatibleVariableOverride]
    "maxdepth": directives.unchanged,
    "caption": directives.unchanged,
  }

  def run(self) -> list[nodes.Node]:
    items = nodes.bullet_list()
    for entry in (line.strip() for line in self.content):
      if entry:
        paragraph = nodes.paragraph()
        paragraph += nodes.reference(entry, _title(entry), refuri=f"{entry}.html")
        items += nodes.list_item("", paragraph)
    return [items]


def _register() -> None:
  roles.register_local_role("doc", _doc_role)  # pyright: ignore[reportArgumentType]
  directives.register_directive("toctree", _TocTree)
  directives.register_directive("code-block", CodeBlock)
  directives.register_directive("api", _docs_api.ApiDirective)
  for name in ("class", "meth", "func", "attr", "data", "exc", "mod"):
    roles.register_local_role(name, _docs_api.role)  # pyright: ignore[reportArgumentType]


def _groups() -> list[tuple[str | None, list[str]]]:
  """The index's toctrees as `(caption, pages)`; unlisted pages go in a last group."""
  index = (_source() / "index.rst").read_text()
  groups: list[tuple[str | None, list[str]]] = []
  for block in re.split(r"^\.\. toctree::\n", index, flags=re.MULTILINE)[1:]:
    caption = re.search(r"^\s+:caption:\s*(.+)$", block, re.MULTILINE)
    entries = re.findall(r"^\s{3,}([\w-]+)\s*$", block, re.MULTILINE)
    groups.append((caption.group(1).strip() if caption else None, entries))
  listed = {page for _, pages in groups for page in pages}
  rest = sorted(_all_pages() - listed - {"index"})
  if rest:
    groups.append(("More", rest))
  return groups


def _pages() -> list[str]:
  return ["index", *(page for _, pages in _groups() for page in pages)]


def _link(caption: str | None, name: str, page: str, tree: dict[str, list[str]]) -> str:
  """One sidebar line: a group title, a page link, or a manual page with its names."""
  if caption:
    return f'<span class="group">{html.escape(caption)}</span>'
  current = " class=current" if name == page else ""
  link = f'<a href="{name}.html"{current}>{html.escape(_title(name))}</a>'
  if name not in tree:
    return link
  opened = " open" if name == page else ""
  inner = "".join(tree[name])
  return f'<details{opened}><summary>{link}</summary><div class="sub">{inner}</div></details>'


def _tree(manual: dict[str, str]) -> dict[str, list[str]]:
  """`{manual page: its top-level names as links}`, from what each page registered."""
  found: dict[str, list[str]] = {page: [] for page in manual}
  for module in _MANUAL:
    page = _manual_page(module)
    depth = module.count(".") + 2
    for full, (where, ident) in _docs_api._registry.items():  # pyright: ignore[reportPrivateUsage]
      if where == page and full.count(".") + 1 == depth:
        found[page].append(
          f'<a href="{page}.html#{ident}">{html.escape(full.rpartition(".")[2])}</a>'
        )
  return found


def _search_index(manual: dict[str, str]) -> list[dict[str, str]]:
  """Everything documented, for the search box: name, full name, kind, summary, link."""
  entries: list[dict[str, str]] = []
  seen: set[str] = set()
  for full, (page, ident) in sorted(_docs_api._registry.items()):  # pyright: ignore[reportPrivateUsage]
    if full in seen:
      continue
    seen.add(full)
    try:
      value = _docs_api.locate(full)
    except LookupError:
      continue
    doc = (
      _docs_api._docstring(value) if callable(value) or inspect.isclass(value) else ""
    )  # pyright: ignore[reportPrivateUsage]
    summary = re.split(r"(?<=[.!?])\s|\n\n", doc.strip(), maxsplit=1)[0].replace(
      "\n", " "
    )[:140]
    entries.append(
      {
        "n": full.rpartition(".")[2],
        "f": full,
        "k": _docs_api._kind(value),  # pyright: ignore[reportPrivateUsage]
        "s": summary,
        "u": f"{page}.html#{ident}",
      }
    )
  for page in [*_pages(), *manual]:
    entries.append(
      {"n": _title(page), "f": page, "k": "page", "s": "", "u": f"{page}.html"}
    )
  return entries


def render(*, strict: bool = False) -> dict[str, bytes]:
  """Every page as HTML, in memory: `{"index.html": ..., ...}`.

  With `strict`, a page that has a problem (a broken reference, an object `api`
  cannot import) raises `DocsError` listing every one.
  """
  _register()
  _docs_api.reset()
  try:
    release = version("discord-micro")
  except PackageNotFoundError:
    release = "development"
  manual = _manual_sources()
  pages = [*_pages(), *manual]
  sources = {
    page: manual[page] if page in manual else (_source() / f"{page}.rst").read_text()
    for page in pages
  }
  for page, text in sources.items():
    _docs_api.register(page, text)
  groups = [*_groups(), ("Manual", list(manual))]
  nav: list[tuple[str | None, str]] = []  # (group caption, "") or (None, page)
  for caption, members in [(None, ["index"]), *groups]:
    if caption:
      nav.append((caption, ""))
    nav.extend((None, name) for name in members)
  tree = _tree(manual)
  problems: list[str] = []
  rendered: dict[str, bytes] = {}
  for page in pages:
    warnings = io.StringIO()
    parts = publish_parts(
      sources[page],
      writer_name="html5",
      settings_overrides={
        "report_level": 2 if strict else 5,
        "halt_level": 5,
        "warning_stream": warnings,
        "syntax_highlight": "none",
        "doctitle_xform": False,
        "initial_header_level": 1,
        "embed_stylesheet": False,
        "stylesheet_path": "",
      },
    )
    problems += [
      f"{page}: {line}" for line in warnings.getvalue().splitlines() if line.strip()
    ]
    links = "\n".join(_link(caption, name, page, tree) for caption, name in nav)
    rendered[f"{page}.html"] = _PAGE.format(
      title=html.escape(_title(page)),
      style=_STYLE,
      version=html.escape(release),
      links=links,
      body=str(parts.get("body", "")),
      script=_SCRIPT,
    ).encode()
  rendered["search.json"] = json.dumps(_search_index(manual)).encode()
  if strict and problems:
    raise DocsError(problems)
  return rendered


class DocsError(Exception):
  """The docs have broken references or unimportable `api` entries."""

  def __init__(self, problems: list[str]) -> None:
    self.problems = problems
    super().__init__("\n".join(problems))


async def serve(*, browser: bool = True) -> None:
  """Serve the docs from memory on 127.0.0.1 until interrupted; writes no files."""
  pages = render()

  class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
      name = self.path.split("?", 1)[0].lstrip("/") or "index.html"
      body = pages.get(name)
      if body is None:
        self.send_error(404)
        return
      self.send_response(200)
      kind = (
        "application/json" if name.endswith(".json") else "text/html; charset=utf-8"
      )
      self.send_header("Content-Type", kind)
      self.send_header("Content-Length", str(len(body)))
      self.end_headers()
      self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
      pass

  server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
  url = f"http://127.0.0.1:{server.server_address[1]}/"
  print(f"Docs at {url} (Ctrl-C to stop)")
  if browser:
    webbrowser.open(url)
  try:
    await asyncio.to_thread(server.serve_forever)
  finally:
    # Ctrl-C cancels this task; stopping the loop lets the worker thread exit.
    server.shutdown()
    server.server_close()
