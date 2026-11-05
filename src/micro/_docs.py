"""`micro docs`: render the bundled ReST docs to HTML and open them.

The docs ship inside the wheel, so they always match the installed Micro. No
build step and nothing written to disk: pages are rendered with docutils in
memory and served on 127.0.0.1 only while the command runs.
"""

import html
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
@media (max-width: 760px) { body { display: block; } nav { width: auto; height: auto;
  position: static; border-right: 0; border-bottom: 1px solid var(--line); }
  main { padding: 1.5rem 1rem 3rem; } }
"""

_PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · Micro</title><style>{style}</style></head>
<body><nav><a class="brand" href="index.html">Micro</a><span class="version">{version}</span>
{links}</nav><main>{body}</main></body></html>
"""

_TITLES: dict[str, str] = {}


def _source() -> Any:
  return resources.files("micro") / "docs"


def _title(name: str) -> str:
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
  return [
    nodes.reference(rawtext, label or _title(target), refuri=f"{target}.html")
  ], []


class _TocTree(Directive):
  has_content = True
  option_spec: ClassVar[dict[str, Any]] = {  # pyright: ignore[reportIncompatibleVariableOverride]
    "maxdepth": directives.unchanged
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


def _pages() -> list[str]:
  """Page order: index, then its toctree, then anything else."""
  index = (_source() / "index.rst").read_text()
  listed = re.findall(
    r"^\s{3,}([\w-]+)\s*$", index.split(".. toctree::", 1)[-1], re.MULTILINE
  )
  every = sorted(
    entry.name.removesuffix(".rst")
    for entry in _source().iterdir()
    if entry.name.endswith(".rst")
  )
  return ["index", *listed, *(page for page in every if page not in {"index", *listed})]


def render() -> dict[str, bytes]:
  """Every page as HTML, in memory: `{"index.html": ..., ...}`."""
  _register()
  try:
    release = version("micro")
  except PackageNotFoundError:
    release = "development"
  pages = _pages()
  rendered: dict[str, bytes] = {}
  for page in pages:
    parts = publish_parts(
      (_source() / f"{page}.rst").read_text(),
      writer_name="html5",
      settings_overrides={
        "report_level": 5,
        "syntax_highlight": "none",
        "doctitle_xform": False,
        "initial_header_level": 1,
        "embed_stylesheet": False,
        "stylesheet_path": "",
      },
    )
    links = "\n".join(
      f'<a href="{name}.html"{" class=current" if name == page else ""}>'
      f"{html.escape(_title(name))}</a>"
      for name in pages
    )
    rendered[f"{page}.html"] = _PAGE.format(
      title=html.escape(_title(page)),
      style=_STYLE,
      version=html.escape(release),
      links=links,
      body=str(parts.get("body", "")),
    ).encode()
  return rendered


def serve(*, browser: bool = True) -> None:
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
      self.send_header("Content-Type", "text/html; charset=utf-8")
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
    server.serve_forever()
  except KeyboardInterrupt:
    pass
  finally:
    server.server_close()
