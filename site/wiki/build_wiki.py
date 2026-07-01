#!/usr/bin/env python3
"""
Gera HTML estático em site/public/wiki/ (pt, default) e/ou site/public/en/wiki/
(en) a partir dos .txt em site/wiki/ e site/wiki/en/. Executar localmente antes
de site/genlanding.py. Não copia para o servidor por si — só o conteúdo de
site/public/ é implantado.

Uso::
    python3 build_wiki.py               # só pt (comportamento de sempre)
    python3 build_wiki.py --locale en   # só en
    python3 build_wiki.py --locale all  # pt + en

Os slugs de arquivo (ex. ``visao-geral``) são os MESMOS entre pt e en — só o
prefixo de URL muda (``/wiki/`` vs ``/en/wiki/``) — para que cada página tenha
um par 1:1 usado nas tags hreflang. As páginas raiz (home, FAQ, junte-se/join)
não são geradas por este script; ver site/public/en/ para os equivalentes
escritos à mão.

Apenas biblioteca padrão Python 3.
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path
from typing import Any, Final

SCRIPT_DIR = Path(__file__).resolve().parent
SITE_DIR = SCRIPT_DIR.parent
ADMIN_DIR = SITE_DIR.parent / "scripts" / "admin"
if str(ADMIN_DIR) not in sys.path:
    sys.path.insert(0, str(ADMIN_DIR))

from admin_guard import ensure_admin_cli

BASE_URL: Final[str] = "https://runv.club"
SITEMAP_PATH = SITE_DIR / "public" / "sitemap.xml"

TXT_GLOB = "[0-9][0-9]_*.txt"
SLUG_RE = re.compile(r"^(\d+)_(.+)\.txt$")

LABELS_PT: Final[dict[str, str]] = {
    "index": "Índice",
    "visao-geral": "Visão geral",
    "contas-e-acesso": "Contas e acesso",
    "regras-da-comunidade": "Regras",
    "punicoes-e-moderacao": "Punições",
    "privacidade-e-seguranca": "Privacidade",
    "faq": "FAQ wiki",
}

LABELS_EN: Final[dict[str, str]] = {
    "index": "Index",
    "visao-geral": "Overview",
    "contas-e-acesso": "Accounts & access",
    "regras-da-comunidade": "Community rules",
    "punicoes-e-moderacao": "Moderation & sanctions",
    "privacidade-e-seguranca": "Privacy & security",
    "faq": "Wiki FAQ",
}

# Config por locale. src_dir/out_dir resolvidos em main() (Path relativos a SITE_DIR).
LOCALES: Final[dict[str, dict[str, Any]]] = {
    "pt": {
        "src_dir": "wiki",
        "out_dir": "public/wiki",
        "url_prefix": "/wiki/",
        "home_href": "/",
        "news_href": "/news/",
        "news_label": "Notícias",
        "join_href": "/junte-se/",
        "join_label": "Junte-se",
        "faq_href": "/faq/",
        "faq_label": "FAQ",
        "admin_label": "Administração:",
        "lang": "pt-BR",
        "og_locale": "pt_BR",
        "og_alt": "runv.club — comunidade brasileira em estilo tilde",
        "labels": LABELS_PT,
        "index_desc": "Início da wiki runv.club: regras, contas, privacidade e FAQ.",
        "index_title": "Wiki — runv.club",
        "sub_desc_suffix": " — wiki runv.club.",
        "sub_title_suffix": " — Wiki runv.club",
        "lang_switch_label": "English",
    },
    "en": {
        "src_dir": "wiki/en",
        "out_dir": "public/en/wiki",
        "url_prefix": "/en/wiki/",
        "home_href": "/en/",
        "news_href": "/en/news/",
        "news_label": "News",
        "join_href": "/en/join/",
        "join_label": "Join",
        "faq_href": "/en/faq/",
        "faq_label": "FAQ",
        "admin_label": "Admin:",
        "lang": "en",
        "og_locale": "en_US",
        "og_alt": "runv.club — a Brazilian tilde-style community",
        "labels": LABELS_EN,
        "index_desc": "Home of the runv.club wiki: rules, accounts, privacy, and FAQ.",
        "index_title": "Wiki — runv.club",
        "sub_desc_suffix": " — runv.club wiki.",
        "sub_title_suffix": " — runv.club Wiki",
        "lang_switch_label": "Português",
    },
}
OTHER_LOCALE: Final[dict[str, str]] = {"pt": "en", "en": "pt"}


def eprint(*args: object) -> None:
    print(*args, file=sys.stderr)


def is_heading_line(s: str) -> bool:
    s = s.strip()
    if not s or len(s) > 120:
        return False
    letters = [c for c in s if c.isalpha()]
    if not letters:
        return False
    return all(c.isupper() for c in letters)


def paragraph_blocks(text: str) -> list[list[str]]:
    lines = text.strip().splitlines()
    blocks: list[list[str]] = []
    cur: list[str] = []
    for line in lines:
        if not line.strip():
            if cur:
                blocks.append(cur)
                cur = []
        else:
            cur.append(line.rstrip())
    if cur:
        blocks.append(cur)
    return blocks


def block_to_html(block: list[str], *, is_first: bool) -> str:
    if len(block) == 1:
        line = block[0].strip()
        if is_first:
            return f'<h1 class="hero-title subpage-title wiki-page-title">{html.escape(line)}</h1>'
        if is_heading_line(line):
            return f"<h2>{html.escape(line)}</h2>"
        return f"<p>{html.escape(line)}</p>"

    stripped = [l.strip() for l in block if l.strip()]
    if stripped and all(
        s.startswith("- ") or s.startswith("– ") or s.startswith("— ") for s in stripped
    ):
        items = []
        for s in stripped:
            for prefix in ("- ", "– ", "— "):
                if s.startswith(prefix):
                    items.append(s[len(prefix) :])
                    break
        lis = "".join(f"<li>{html.escape(i)}</li>" for i in items)
        return f"<ul>{lis}</ul>"

    inner = "<br>\n".join(html.escape(l) for l in block)
    return f"<p>{inner}</p>"


def txt_to_article_body(raw: str) -> str:
    blocks = paragraph_blocks(raw)
    parts: list[str] = []
    for i, b in enumerate(blocks):
        parts.append(block_to_html(b, is_first=(i == 0)))
    return "\n\n".join(parts)


def wiki_url(locale_key: str, slug: str) -> str:
    prefix = LOCALES[locale_key]["url_prefix"]
    if slug == "index":
        return f"{BASE_URL}{prefix}"
    return f"{BASE_URL}{prefix}{slug}.html"


def page_shell(
    *,
    locale_key: str,
    title: str,
    description: str,
    body_main: str,
    nav_pages: list[tuple[str, str]],
    current_slug: str | None,
    available_locales: set[str],
) -> str:
    cfg = LOCALES[locale_key]
    nav_items = []
    for slug, label in nav_pages:
        if current_slug is not None and slug == current_slug:
            nav_items.append(
                f'<span class="hero-nav-current" aria-current="page">{html.escape(label)}</span>'
            )
        else:
            href = cfg["url_prefix"] if slug == "index" else f'{cfg["url_prefix"]}{slug}.html'
            nav_items.append(f'<a href="{html.escape(href, quote=True)}">{html.escape(label)}</a>')
    nav_inner = '\n        <span class="hero-nav-sep" aria-hidden="true">·</span>\n        '.join(
        nav_items
    )

    slug_for_url = current_slug or "index"
    canonical = wiki_url(locale_key, slug_for_url)

    # Só emite hreflang quando as duas variantes existem de fato — evita
    # apontar para uma versão que ainda não foi gerada.
    hreflang_block = ""
    if {"pt", "en"} <= available_locales:
        hreflang_map = {
            "pt-BR": wiki_url("pt", slug_for_url),
            "en": wiki_url("en", slug_for_url),
            "x-default": wiki_url("pt", slug_for_url),
        }
        hreflang_block = (
            "\n".join(
                f'  <link rel="alternate" hreflang="{code}" href="{html.escape(url, quote=True)}">'
                for code, url in hreflang_map.items()
            )
            + "\n"
        )

    lang_switch = ""
    other = OTHER_LOCALE[locale_key]
    if other in available_locales:
        other_href = (
            LOCALES[other]["url_prefix"]
            if slug_for_url == "index"
            else f'{LOCALES[other]["url_prefix"]}{slug_for_url}.html'
        )
        lang_switch = (
            f'\n        <span class="hero-nav-sep" aria-hidden="true">·</span>\n'
            f'        <a href="{html.escape(other_href, quote=True)}" class="lang-switch">{html.escape(cfg["lang_switch_label"])}</a>'
        )

    return f"""<!DOCTYPE html>
<html lang="{cfg['lang']}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <meta name="description" content="{html.escape(description)}">
  <link rel="canonical" href="{html.escape(canonical, quote=True)}">
{hreflang_block}
  <meta name="robots" content="index, follow">
  <meta name="theme-color" content="#0c0b0f">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{html.escape(canonical, quote=True)}">
  <meta property="og:locale" content="{cfg['og_locale']}">
  <meta property="og:site_name" content="runv.club">
  <meta property="og:title" content="{html.escape(title)}">
  <meta property="og:description" content="{html.escape(description)}">
  <meta property="og:image" content="{BASE_URL}/assets/og-image.png">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="{html.escape(cfg['og_alt'])}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{html.escape(title)}">
  <meta name="twitter:description" content="{html.escape(description)}">
  <meta name="twitter:image" content="{BASE_URL}/assets/og-image.png">
  <link rel="icon" href="/favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="../assets/style.css">
</head>
<body>
  <div class="wrap">
    <nav class="top-nav"><a href="{html.escape(cfg['home_href'], quote=True)}">← runv.club</a></nav>

    <header>
      <p class="eyebrow">runv.club</p>
      <nav class="hero-nav wiki-hero-nav" aria-label="Páginas da wiki">
        <a href="{html.escape(cfg['news_href'], quote=True)}">{html.escape(cfg['news_label'])}</a>
        <span class="hero-nav-sep" aria-hidden="true">·</span>
        {nav_inner}
        <span class="hero-nav-sep" aria-hidden="true">·</span>
        <a href="{html.escape(cfg['join_href'], quote=True)}">{html.escape(cfg['join_label'])}</a>{lang_switch}
      </nav>
    </header>

    <main class="section prose-block subpage-main wiki-main">
{body_main}
    </main>

    <footer class="site-footer">
      <p>{html.escape(cfg['admin_label'])} <a href="mailto:admin@runv.club">admin@runv.club</a><span class="footer-sep" aria-hidden="true"> · </span><a href="{html.escape(cfg['faq_href'], quote=True)}" class="footer-link-discrete">{html.escape(cfg['faq_label'])}</a></p>
    </footer>
  </div>
</body>
</html>
"""


def slug_and_label(path: Path, labels: dict[str, str]) -> tuple[str, str] | None:
    m = SLUG_RE.match(path.name)
    if not m:
        return None
    slug = m.group(2)
    label = labels.get(slug, slug.replace("-", " ").title())
    return slug, label


def first_line_title(raw: str) -> str:
    for line in raw.strip().splitlines():
        t = line.strip()
        if t:
            return t[:70] + ("…" if len(t) > 70 else "")
    return "Wiki"


def build_nav_order(paths: list[Path], labels: dict[str, str]) -> list[tuple[str, str]]:
    ordered: list[tuple[str, str]] = []
    for p in sorted(paths):
        sl = slug_and_label(p, labels)
        if sl:
            ordered.append(sl)
    idx = next((i for i, (s, _) in enumerate(ordered) if s == "index"), None)
    if idx is not None and idx > 0:
        ordered.insert(0, ordered.pop(idx))
    return ordered


def patch_sitemap(urls: list[str]) -> None:
    if not SITEMAP_PATH.is_file():
        return
    text = SITEMAP_PATH.read_text(encoding="utf-8")
    marker_start = "  <!-- wiki:gerado -->"
    marker_end = "  <!-- /wiki:gerado -->"
    block_lines = [marker_start]
    for url in urls:
        block_lines.append("  <url>")
        block_lines.append(f"    <loc>{html.escape(url)}</loc>")
        block_lines.append("  </url>")
    block_lines.append(marker_end)
    new_block = "\n".join(block_lines) + "\n"

    if marker_start in text and marker_end in text:
        before, rest = text.split(marker_start, 1)
        _, after = rest.split(marker_end, 1)
        text = before + new_block + after.lstrip("\n")
    else:
        text = text.replace("</urlset>", new_block + "</urlset>", 1)
    SITEMAP_PATH.write_text(text, encoding="utf-8")


def build_locale(locale_key: str, *, available_locales: set[str]) -> list[str]:
    cfg = LOCALES[locale_key]
    src_dir = SITE_DIR / cfg["src_dir"]
    out_dir = SITE_DIR / cfg["out_dir"]
    labels = cfg["labels"]

    txt_files = sorted(src_dir.glob(TXT_GLOB))
    if not txt_files:
        eprint(f"[{locale_key}] Nenhum ficheiro {TXT_GLOB} em {src_dir}")
        return []

    out_dir.mkdir(parents=True, exist_ok=True)
    nav_pages = build_nav_order(txt_files, labels)
    urls: list[str] = [wiki_url(locale_key, "index")]

    for path in txt_files:
        sl = slug_and_label(path, labels)
        if not sl:
            continue
        slug, _label = sl
        raw = path.read_text(encoding="utf-8")
        title_line = first_line_title(raw)
        article = txt_to_article_body(raw)

        if slug == "index":
            body_main = article
            out_name = "index.html"
            current = "index"
            desc = cfg["index_desc"]
            full_title = cfg["index_title"]
        else:
            body_main = article
            out_name = f"{slug}.html"
            current = slug
            desc = f"{title_line}{cfg['sub_desc_suffix']}"
            full_title = f"{title_line}{cfg['sub_title_suffix']}"
            urls.append(wiki_url(locale_key, slug))

        html_out = page_shell(
            locale_key=locale_key,
            title=full_title,
            description=desc,
            body_main=body_main,
            nav_pages=nav_pages,
            current_slug=current,
            available_locales=available_locales,
        )
        (out_dir / out_name).write_text(html_out, encoding="utf-8")
        print(f"[{locale_key}] Wrote", out_dir / out_name)

    return urls


def main() -> int:
    ap = argparse.ArgumentParser(description="Gera a wiki estática (pt e/ou en)")
    ap.add_argument(
        "--locale",
        choices=["pt", "en", "all"],
        default="pt",
        help="qual wiki gerar (default: pt, igual ao comportamento anterior)",
    )
    args = ap.parse_args()
    ensure_admin_cli(script_name=Path(__file__).name)

    keys = ["pt", "en"] if args.locale == "all" else [args.locale]
    available_locales = {
        k for k in ("pt", "en") if any((SITE_DIR / LOCALES[k]["src_dir"]).glob(TXT_GLOB))
    }

    all_urls: list[str] = []
    built_any = False
    for key in keys:
        urls = build_locale(key, available_locales=available_locales)
        if urls:
            built_any = True
        all_urls.extend(urls)

    if not built_any:
        return 1

    patch_sitemap(sorted(set(all_urls)))
    print("Updated", SITEMAP_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
