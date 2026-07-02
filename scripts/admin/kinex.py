#!/usr/bin/env python3
"""
kinex — gateway HTTP → **Nex** para runv.club (stdlib puro).

Expõe a mesma árvore que o nexd (``/var/nex`` + ``/home/<user>/public_nex``) num
navegador web comum, convertendo texto Nex em HTML. Corre atrás do Apache no
prefixo ``/nex`` (ver site/genlanding.py: ProxyPass /nex → 127.0.0.1:1971).

Reutiliza a lógica do nexd (mesmo saneamento de selector e mesma resolução de
caminho — logo a **mesma proteção anti-traversal**). Não abre sockets Nex: chama
diretamente as funções puras de ``nexd`` sobre o sistema de ficheiros.

Versão 0.01 — runv.club
"""

from __future__ import annotations

import argparse
import html
import logging
import re
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Final
from urllib.parse import unquote

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

import nexd  # servidor Nex: NexConfig, sanitize_selector, resolve_selector_path, ...

VERSION: Final[str] = "0.01"

DEFAULT_HOST: Final[str] = "127.0.0.1"
DEFAULT_PORT: Final[int] = 1971
DEFAULT_BASE_PATH: Final[str] = "/nex"

# Extensões servidas como ficheiro cru (não convertidas para HTML).
RAW_CONTENT_TYPES: Final[dict[str, str]] = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
    ".pdf": "application/pdf",
}

_LINK_RE: Final[re.Pattern[str]] = re.compile(r"^=>\s*(\S+)(?:\s+(.*))?$")

PAGE_CSS: Final[str] = """
:root { color-scheme: light dark; }
body { margin:0; background:#efe9dd; color:#2b2620;
  font:16px/1.6 "IBM Plex Mono", ui-monospace, "Cascadia Code", Consolas, monospace; }
.wrap { max-width:44rem; margin:0 auto; padding:2.2rem 1.3rem 4rem; }
h1,h2,h3 { font-family: inherit; line-height:1.25; }
h1 { font-size:1.5rem; } h2 { font-size:1.25rem; } h3 { font-size:1.08rem; }
a { color:#7a4b00; text-underline-offset:3px; }
a:hover { color:#111; }
pre { background:#e4dcc9; padding:.8rem 1rem; overflow-x:auto; border-radius:4px; }
.nav { margin-bottom:1.4rem; font-size:.9rem; opacity:.8; }
.linkline { display:block; padding:.08rem 0; }
footer { margin-top:2.5rem; font-size:.82rem; opacity:.65; border-top:1px solid #cdc3ac; padding-top:1rem; }
@media (prefers-color-scheme: dark) {
  body { background:#14120e; color:#e6dcc6; }
  a { color:#e0b871; } a:hover { color:#fff; }
  pre { background:#211d15; } footer { border-color:#3a3324; }
}
"""


def setup_logging(verbose: bool) -> logging.Logger:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    return logging.getLogger("kinex")


def _resolve_link_target(raw_target: str, current_selector: str, base_path: str) -> str | None:
    """
    Converte um alvo de link Nex (``=> alvo``) num href HTTP sob ``base_path``.
    URLs externas (com esquema) passam intactas; ``nex://`` vira um link http local
    apenas se apontar ao próprio host? — mantemos simples: nex:// externos ficam como estão.
    """
    t = raw_target.strip()
    if not t:
        return None
    # Link absoluto com esquema (http, https, gemini, gopher, mailto, nex externo): manter.
    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", t) or t.startswith("mailto:"):
        return t
    # Selector Nex absoluto (/...) ou relativo — resolver contra o selector atual.
    if t.startswith("/"):
        sel = t
    else:
        base_dir = current_selector if current_selector.endswith("/") else current_selector.rsplit("/", 1)[0] + "/"
        sel = base_dir + t
    try:
        sel = nexd.sanitize_selector(sel)
    except ValueError:
        return None
    return base_path.rstrip("/") + sel


def nex_to_html_body(text: str, current_selector: str, base_path: str) -> str:
    """Converte conteúdo Nex (texto) num fragmento HTML seguro."""
    out: list[str] = []
    in_pre = False
    for line in text.split("\n"):
        if line.startswith("```"):
            if in_pre:
                out.append("</pre>")
                in_pre = False
            else:
                out.append("<pre>")
                in_pre = True
            continue
        if in_pre:
            out.append(html.escape(line))
            continue
        m = _LINK_RE.match(line)
        if m:
            target, label = m.group(1), (m.group(2) or m.group(1))
            href = _resolve_link_target(target, current_selector, base_path)
            if href is None:
                out.append(f'<span class="linkline">{html.escape(label)}</span>')
            else:
                out.append(
                    f'<a class="linkline" href="{html.escape(href, quote=True)}">'
                    f"{html.escape(label)}</a>"
                )
            continue
        if line.startswith("### "):
            out.append(f"<h3>{html.escape(line[4:])}</h3>")
        elif line.startswith("## "):
            out.append(f"<h2>{html.escape(line[3:])}</h2>")
        elif line.startswith("# "):
            out.append(f"<h1>{html.escape(line[2:])}</h1>")
        elif line.strip() == "":
            out.append("")
        else:
            out.append(f"{html.escape(line)}<br>")
    if in_pre:
        out.append("</pre>")
    return "\n".join(out)


def render_html_page(title: str, body_html: str, base_path: str) -> bytes:
    root_href = html.escape(base_path.rstrip("/") + "/", quote=True)
    doc = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)} — Nex — runv.club</title>
<style>{PAGE_CSS}</style>
</head>
<body>
<div class="wrap">
<div class="nav"><a href="{root_href}">nex://runv.club/</a> · gateway HTTP → Nex</div>
{body_html}
<footer>Servido por kinex — gateway Nex do runv.club. Para a experiência nativa: <code>rex</code> no terminal, ou um cliente Nex na porta 1900.</footer>
</div>
</body>
</html>
"""
    return doc.encode("utf-8")


def members_body_html(cfg: nexd.NexConfig, base_path: str) -> str:
    lines = ["<h1>Cápsulas Nex dos membros</h1>", "<p>Membros do runv.club com espaço Nex:</p>"]
    members = nexd.list_member_usernames(cfg)
    if not members:
        lines.append("<p>(ainda sem cápsulas Nex publicadas)</p>")
    else:
        for name in members:
            href = html.escape(base_path.rstrip("/") + f"/users/{name}/", quote=True)
            lines.append(f'<a class="linkline" href="{href}">~{html.escape(name)}</a>')
    return "\n".join(lines)


class KinexHandler(BaseHTTPRequestHandler):
    server_version = f"kinex/{VERSION}"

    @property
    def cfg(self) -> nexd.NexConfig:
        return self.server.cfg  # type: ignore[attr-defined]

    @property
    def base_path(self) -> str:
        return self.server.base_path  # type: ignore[attr-defined]

    @property
    def log(self) -> logging.Logger:
        return self.server.log  # type: ignore[attr-defined]

    def log_message(self, fmt: str, *args) -> None:  # silencia o log default do http.server
        self.log.debug("%s - %s", self.address_string(), fmt % args)

    def _send(self, status: int, body: bytes, content_type: str = "text/html; charset=utf-8") -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def do_HEAD(self) -> None:
        self.do_GET()

    def do_GET(self) -> None:
        raw_path = unquote(self.path.split("?", 1)[0])
        bp = self.base_path.rstrip("/")
        # Mapeia o caminho HTTP para um selector Nex.
        if raw_path == bp or raw_path == bp + "/":
            selector = "/"
        elif raw_path.startswith(bp + "/"):
            selector = raw_path[len(bp):]
        else:
            selector = raw_path  # atrás do proxy o Apache já entrega /nex/...
        try:
            selector = nexd.sanitize_selector(selector)
        except ValueError:
            self._send(404, render_html_page("404", "<h1>404</h1><p>Selector inválido.</p>", self.base_path))
            return

        kind, path, username = nexd.resolve_selector_path(self.cfg, selector)

        if kind == "users_index":
            self._send(200, render_html_page("membros", members_body_html(self.cfg, self.base_path), self.base_path))
            return

        # Ficheiro binário (imagem, pdf): servir cru com content-type adequado.
        if path is not None and path.is_file():
            ext = path.suffix.lower()
            if ext in RAW_CONTENT_TYPES:
                try:
                    self._send(200, path.read_bytes(), RAW_CONTENT_TYPES[ext])
                except OSError:
                    self._send(404, render_html_page("404", "<h1>404</h1>", self.base_path))
                return

        # Restante (index, listagem, ficheiros de texto): reutiliza o nexd e converte para HTML.
        try:
            nex_bytes = nexd.build_response(self.cfg, selector, self.log)
        except Exception as e:  # pragma: no cover
            self.log.warning("erro a servir %r: %s", selector, e)
            self._send(500, render_html_page("erro", "<h1>500</h1>", self.base_path))
            return
        text = nex_bytes.decode("utf-8", errors="replace")
        title = selector.strip("/").split("/")[-1] or "runv.club"
        body = nex_to_html_body(text, selector, self.base_path)
        status = 404 if text.startswith("# 404") else 200
        self._send(status, render_html_page(title, body, self.base_path))


class KinexServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, addr, handler, cfg: nexd.NexConfig, base_path: str, log: logging.Logger):
        self.cfg = cfg
        self.base_path = base_path
        self.log = log
        super().__init__(addr, handler)


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Gateway HTTP → Nex (kinex) do runv.club.")
    p.add_argument("--root", type=Path, default=nexd.DEFAULT_ROOT)
    p.add_argument("--homes-root", type=Path, default=nexd.DEFAULT_HOMES_ROOT)
    p.add_argument("--host", default=DEFAULT_HOST)
    p.add_argument("--port", type=int, default=DEFAULT_PORT)
    p.add_argument("--hostname", default="runv.club")
    p.add_argument("--base-path", default=DEFAULT_BASE_PATH, help="prefixo HTTP (padrão /nex)")
    p.add_argument("--verbose", action="store_true")
    p.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    log = setup_logging(args.verbose)
    cfg = nexd.NexConfig(root=args.root, homes_root=args.homes_root, hostname=args.hostname)
    server = KinexServer((args.host, args.port), KinexHandler, cfg, args.base_path, log)
    log.info("kinex %s em http://%s:%d%s (root=%s)", VERSION, args.host, args.port, args.base_path, cfg.root)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("a terminar (SIGINT)")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
