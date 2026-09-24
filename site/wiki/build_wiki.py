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

if str(SITE_DIR) not in sys.path:
    sys.path.insert(0, str(SITE_DIR))
import chrome  # noqa: E402

BASE_URL: Final[str] = chrome.BASE_URL
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
    "small-web-nex": "Small web",
    "i2p-eepsites": "I2P",
}

LABELS_EN: Final[dict[str, str]] = {
    "index": "Index",
    "visao-geral": "Overview",
    "contas-e-acesso": "Accounts & access",
    "regras-da-comunidade": "Community rules",
    "punicoes-e-moderacao": "Moderation & sanctions",
    "privacidade-e-seguranca": "Privacy & security",
    "faq": "Wiki FAQ",
    "small-web-nex": "Small web",
    "i2p-eepsites": "I2P",
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
        "nav_label": "Páginas da wiki",
        "stamp": "wiki",
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
        "nav_label": "Wiki pages",
        "stamp": "wiki",
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
            return f'<h1 class="title">{html.escape(line)}</h1>'
        if line.startswith("## "):
            return f"<h2>{html.escape(line[3:].strip())}</h2>"
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
    slug_for_url = current_slug or "index"

    items = []
    for slug, label in nav_pages:
        href = cfg["url_prefix"] if slug == "index" else f'{cfg["url_prefix"]}{slug}.html'
        cur = ' aria-current="page"' if slug == slug_for_url else ""
        items.append(f'<li><a href="{html.escape(href, quote=True)}"{cur}>{html.escape(label)}</a></li>')
    wiki_nav = (
        f'<nav class="wiki-nav" aria-label="{html.escape(cfg["nav_label"], quote=True)}">\n'
        f'      <p class="cmd">ls {html.escape(cfg["url_prefix"])}</p>\n'
        '      <ul>' + "".join(items) + "</ul>\n    </nav>"
    )

    def path_for(loc: str) -> str:
        prefix = LOCALES[loc]["url_prefix"]
        return prefix if slug_for_url == "index" else f"{prefix}{slug_for_url}.html"

    alternates = None
    if {"pt", "en"} <= available_locales:
        alternates = {"pt-BR": path_for("pt"), "en": path_for("en"), "x-default": path_for("pt")}
    other = OTHER_LOCALE[locale_key]
    other_href = path_for(other) if other in available_locales else None

    head_html = chrome.head(
        locale=locale_key,
        title=title,
        description=description,
        canonical=path_for(locale_key),
        alternates=alternates,
    )
    body = f"""    <p class="cmd">less {html.escape(path_for(locale_key))}</p>
    <article class="prose">
{body_main}
    </article>

    {wiki_nav}"""
    return chrome.document(
        locale=locale_key,
        head_html=head_html,
        current="wiki",
        stamp=cfg["stamp"],
        other_href=other_href,
        body=body,
    )


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
