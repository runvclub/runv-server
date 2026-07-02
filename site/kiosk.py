#!/usr/bin/env python3
"""
kiosk — agregador estático de blogs/journals dos membros do runv.club.

Inspirado no *the-neon-kiosk* de ~m15o: lê uma lista **opt-in** de páginas de
membros nos formatos **HTML Blog** (``<h1>`` + ``<time>`` + ``<a>``) e
**HTML Journal** (``<h1>`` + ``<article>`` com ``<h2>``), busca cada uma, filtra
as entradas recentes e gera uma página estática ``/recentes/`` — uma camada de
descoberta que complementa a constelação (quem existe) com atividade (o que é novo).

Segurança (conteúdo remoto é NÃO confiável):
- Só ``stdlib`` (urllib, html.parser). Timeout e limite de tamanho por fonte.
- **Nunca** injeta HTML remoto cru: só texto escapado + links absolutos http(s)
  validados. É o mesmo princípio do endurecimento anti-XSS de publish_news.py.
- Falha de uma fonte nunca derruba a geração; o que foi ignorado é registado.

Opt-in: uma fonte por linha em ``site/kiosk-sources.txt`` (``#`` = comentário).
Formato de linha:  <url>            (título vem do <h1> da página)
             ou:   <url> | <rótulo> (rótulo força o nome da fonte)

Uso típico (cron/admin, não precisa de root):
    python3 site/kiosk.py --days 45

Versão 0.01 — runv.club
"""

from __future__ import annotations

import argparse
import html
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Final
from urllib.parse import urljoin, urlparse

VERSION: Final[str] = "0.01"

_SITE_DIR: Final[Path] = Path(__file__).resolve().parent
DEFAULT_SOURCES: Final[Path] = _SITE_DIR / "kiosk-sources.txt"
DEFAULT_OUT_DIR: Final[Path] = _SITE_DIR / "public" / "recentes"
DEFAULT_DAYS: Final[int] = 45
DEFAULT_TIMEOUT: Final[float] = 12.0
DEFAULT_MAX_BYTES: Final[int] = 2_000_000
DEFAULT_LIMIT: Final[int] = 60
USER_AGENT: Final[str] = f"runv-kiosk/{VERSION} (+https://runv.club/recentes/)"

_DATE_RE = __import__("re").compile(r"(\d{4})-(\d{2})-(\d{2})")


@dataclass
class Entry:
    date: datetime
    title: str
    url: str
    source_title: str
    source_url: str


def _parse_iso_date(text: str) -> datetime | None:
    m = _DATE_RE.search(text or "")
    if not m:
        return None
    try:
        return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), tzinfo=timezone.utc)
    except ValueError:
        return None


def _safe_abs_url(base: str, href: str) -> str | None:
    """Resolve href contra base e só aceita http/https absolutos."""
    if not href:
        return None
    try:
        abs_url = urljoin(base, href.strip())
        parsed = urlparse(abs_url)
    except ValueError:
        return None
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return None
    return abs_url


class _BlogParser(HTMLParser):
    """
    HTML Blog: título do documento no primeiro <h1>; entradas emparelham um
    <time datetime> com o <a href> seguinte (texto do link = título da entrada).
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.site_title = ""
        self.entries: list[tuple[datetime, str, str]] = []  # (date, href, text)
        self._in_h1 = False
        self._got_h1 = False
        self._pending_date: datetime | None = None
        self._in_time = False
        self._time_dt: str | None = None
        self._time_text: list[str] = []
        self._in_a = False
        self._a_href: str | None = None
        self._a_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        d = dict(attrs)
        if tag == "h1" and not self._got_h1:
            self._in_h1 = True
        elif tag == "time":
            self._in_time = True
            self._time_dt = d.get("datetime")
            self._time_text = []
        elif tag == "a":
            self._in_a = True
            self._a_href = d.get("href")
            self._a_text = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "h1" and self._in_h1:
            self._in_h1 = False
            self._got_h1 = True
        elif tag == "time" and self._in_time:
            self._in_time = False
            dt = _parse_iso_date(self._time_dt or "".join(self._time_text))
            if dt is not None:
                self._pending_date = dt
        elif tag == "a" and self._in_a:
            self._in_a = False
            text = "".join(self._a_text).strip()
            if self._pending_date is not None and self._a_href:
                self.entries.append((self._pending_date, self._a_href, text or "(sem título)"))
                self._pending_date = None

    def handle_data(self, data: str) -> None:
        if self._in_h1 and not self.site_title:
            self.site_title = data.strip()
        if self._in_time:
            self._time_text.append(data)
        if self._in_a:
            self._a_text.append(data)


class _JournalParser(HTMLParser):
    """
    HTML Journal: título no <h1>; cada <article> tem um <h2> (data/título). O link
    da entrada é a própria página (journals são uma página só).
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.site_title = ""
        self.entries: list[tuple[datetime | None, str]] = []  # (date, h2 text)
        self._in_h1 = False
        self._got_h1 = False
        self._in_article = False
        self._in_h2 = False
        self._h2_text: list[str] = []
        self._article_has_h2 = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "h1" and not self._got_h1:
            self._in_h1 = True
        elif tag == "article":
            self._in_article = True
            self._article_has_h2 = False
        elif tag == "h2" and self._in_article and not self._article_has_h2:
            self._in_h2 = True
            self._h2_text = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "h1" and self._in_h1:
            self._in_h1 = False
            self._got_h1 = True
        elif tag == "article" and self._in_article:
            self._in_article = False
        elif tag == "h2" and self._in_h2:
            self._in_h2 = False
            self._article_has_h2 = True
            text = "".join(self._h2_text).strip()
            if text:
                self.entries.append((_parse_iso_date(text), text))

    def handle_data(self, data: str) -> None:
        if self._in_h1 and not self.site_title:
            self.site_title = data.strip()
        if self._in_h2:
            self._h2_text.append(data)


def fetch(url: str, *, timeout: float, max_bytes: int) -> str | None:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (opt-in http(s))
            ctype = resp.headers.get("Content-Type", "")
            if "html" not in ctype and "text" not in ctype and ctype:
                return None
            raw = resp.read(max_bytes + 1)
    except (urllib.error.URLError, OSError, ValueError):
        return None
    if len(raw) > max_bytes:
        raw = raw[:max_bytes]
    return raw.decode("utf-8", errors="replace")


def entries_from_source(
    source_url: str,
    label: str | None,
    html_text: str,
    *,
    cutoff: datetime,
) -> list[Entry]:
    is_journal = "<article" in html_text.lower()
    out: list[Entry] = []
    if is_journal:
        jp = _JournalParser()
        jp.feed(html_text)
        site_title = label or jp.site_title or _host_of(source_url)
        for dt, title in jp.entries:
            if dt is None or dt < cutoff:
                continue
            out.append(Entry(date=dt, title=title, url=source_url, source_title=site_title, source_url=source_url))
    else:
        bp = _BlogParser()
        bp.feed(html_text)
        site_title = label or bp.site_title or _host_of(source_url)
        for dt, href, text in bp.entries:
            if dt < cutoff:
                continue
            abs_url = _safe_abs_url(source_url, href)
            if abs_url is None:
                continue
            out.append(Entry(date=dt, title=text, url=abs_url, source_title=site_title, source_url=source_url))
    return out


def _host_of(url: str) -> str:
    try:
        return urlparse(url).netloc or url
    except ValueError:
        return url


def load_sources(path: Path) -> list[tuple[str, str | None]]:
    if not path.is_file():
        return []
    out: list[tuple[str, str | None]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if "|" in s:
            url, label = s.split("|", 1)
            url, label = url.strip(), label.strip() or None
        else:
            url, label = s, None
        if urlparse(url).scheme in ("http", "https"):
            out.append((url, label))
    return out


def render_page(entries: list[Entry], *, generated_at: datetime) -> str:
    rows: list[str] = []
    for e in entries:
        d = e.date.strftime("%Y-%m-%d")
        rows.append(
            '        <li class="kiosk-item">\n'
            f'          <time datetime="{html.escape(d, quote=True)}">{html.escape(d)}</time>\n'
            f'          <a href="{html.escape(e.url, quote=True)}">{html.escape(e.title)}</a>\n'
            f'          <span class="kiosk-src">— {html.escape(e.source_title)}</span>\n'
            "        </li>"
        )
    listing = "\n".join(rows) if rows else '        <li class="kiosk-empty">Ainda sem entradas recentes. Publique um blog ou journal e peça para entrar na lista.</li>'
    gen = generated_at.strftime("%Y-%m-%d %H:%M UTC")
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Recentes — blogs e journals — runv.club</title>
  <meta name="description" content="Entradas recentes de blogs e journals dos membros do runv.club, no formato HTML Blog/Journal da small web.">
  <link rel="canonical" href="https://runv.club/recentes/">
  <meta name="robots" content="index, follow">
  <meta name="theme-color" content="#0c0b0f">
  <link rel="icon" href="/favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="/assets/style.css">
</head>
<body>
  <div class="page-root">
  <div class="wrap">
    <header class="hero">
      <nav class="hero-nav" aria-label="Outras páginas">
        <a href="/">Início</a>
        <span class="hero-nav-sep" aria-hidden="true">·</span>
        <a href="/news/">Notícias</a>
        <span class="hero-nav-sep" aria-hidden="true">·</span>
        <a href="/wiki/">Wiki</a>
        <span class="hero-nav-sep" aria-hidden="true">·</span>
        <a href="/nex/">Nex</a>
      </nav>
      <h1 class="hero-title">Recentes</h1>
      <p class="hero-subtitle">Blogs e journals dos membros, no formato HTML Blog/Journal da small web. Publique o seu e peça para entrar na lista.</p>
    </header>
    <section class="section">
      <ul class="kiosk-list">
{listing}
      </ul>
      <p class="section-kicker" style="margin-top:2rem">Gerado em {gen} · {len(entries)} entrada(s)</p>
    </section>
    <footer class="site-footer">
      <p>Administração: <a href="mailto:admin@runv.club">admin@runv.club</a></p>
    </footer>
  </div>
  </div>
</body>
</html>
"""


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Agrega blogs/journals dos membros numa página /recentes estática.")
    p.add_argument("--sources", type=Path, default=DEFAULT_SOURCES, help=f"lista opt-in (padrão {DEFAULT_SOURCES})")
    p.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR, help=f"pasta de saída (padrão {DEFAULT_OUT_DIR})")
    p.add_argument("--days", type=int, default=DEFAULT_DAYS, help=f"janela de recência em dias (padrão {DEFAULT_DAYS})")
    p.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    p.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    p.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help=f"máximo de entradas (padrão {DEFAULT_LIMIT})")
    p.add_argument("--now", default=None, help="timestamp ISO fixo para geração (testes); padrão: agora UTC")
    p.add_argument("--dry-run", action="store_true", help="não escreve o ficheiro; só relata")
    p.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    args = p.parse_args(argv)

    if args.now:
        try:
            now = datetime.fromisoformat(args.now)
            if now.tzinfo is None:
                now = now.replace(tzinfo=timezone.utc)
        except ValueError:
            print(f"--now inválido: {args.now!r}", file=sys.stderr)
            return 2
    else:
        now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=args.days)

    sources = load_sources(args.sources)
    if not sources:
        print(f"kiosk: nenhuma fonte em {args.sources} (uma URL por linha). Nada a gerar.", file=sys.stderr)

    all_entries: list[Entry] = []
    skipped: list[str] = []
    for url, label in sources:
        text = fetch(url, timeout=args.timeout, max_bytes=args.max_bytes)
        if text is None:
            skipped.append(url)
            print(f"  [skip] {url} (inacessível ou não-HTML)", file=sys.stderr)
            continue
        found = entries_from_source(url, label, text, cutoff=cutoff)
        print(f"  [ok]   {url} — {len(found)} entrada(s) na janela")
        all_entries.extend(found)

    all_entries.sort(key=lambda e: e.date, reverse=True)
    if len(all_entries) > args.limit:
        print(f"  [nota] {len(all_entries)} entradas → limitado a {args.limit}", file=sys.stderr)
        all_entries = all_entries[: args.limit]

    page = render_page(all_entries, generated_at=now)

    if args.dry_run:
        print(f"[dry-run] geraria {args.out_dir / 'index.html'} com {len(all_entries)} entrada(s); "
              f"{len(skipped)} fonte(s) ignorada(s).")
        return 0

    args.out_dir.mkdir(parents=True, exist_ok=True)
    out = args.out_dir / "index.html"
    out.write_text(page, encoding="utf-8")
    print(f"kiosk: {out} escrito ({len(all_entries)} entrada(s); {len(sources)} fonte(s), {len(skipped)} ignorada(s)).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
