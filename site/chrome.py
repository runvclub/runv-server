"""
Moldura comum das páginas do runv.club (visual "formulário contínuo").

Usado pelos geradores (build_home.py, wiki/build_wiki.py, kiosk.py) para que
cabeçalho, navegação e rodapé sejam iguais em todo o site. As páginas escritas
à mão em site/public/ (junte-se, faq, news, now) copiam esta mesma marcação;
ao mudar algo aqui, actualize-as também.

Apenas biblioteca padrão Python 3.
"""

from __future__ import annotations

import html
from typing import Final

BASE_URL: Final[str] = "https://runv.club"
THEME_COLOR: Final[str] = "#8a8f84"

# (chave, href, rótulo). A chave identifica a página actual (aria-current).
NAV: Final[dict[str, list[tuple[str, str, str]]]] = {
    "pt": [
        ("home", "/", "início"),
        ("join", "/junte-se/", "junte-se"),
        ("wiki", "/wiki/", "wiki"),
        ("news", "/news/", "notícias"),
        ("recentes", "/recentes/", "recentes"),
        ("now", "/now/", "agora"),
    ],
    "en": [
        ("home", "/en/", "home"),
        ("join", "/en/join/", "join"),
        ("wiki", "/en/wiki/", "wiki"),
        ("news", "/en/news/", "news"),
        ("recentes", "/recentes/", "recent (pt)"),
        ("now", "/en/now/", "now"),
    ],
}

LANG_ATTR: Final[dict[str, str]] = {"pt": "pt-BR", "en": "en"}
OG_LOCALE: Final[dict[str, str]] = {"pt": "pt_BR", "en": "en_US"}
OTHER_LABEL: Final[dict[str, str]] = {"pt": "english", "en": "português"}

FOOTER: Final[dict[str, dict[str, str]]] = {
    "pt": {
        "write": "contato:",
        "rss": "RSS",
        "badge_hint": "botão 88x31 para linkar o runv.club",
        "tilde": "tildeverse",
    },
    "en": {
        "write": "contact:",
        "rss": "RSS",
        "badge_hint": "88x31 button for linking to runv.club",
        "tilde": "tildeverse",
    },
}

BADGES: Final[list[tuple[str, str]]] = [
    ("runv-club.svg", "runv.club"),
    ("debian.svg", "Debian"),
    ("feito-no-brasil.svg", "feito no Brasil"),
    ("rss.svg", "RSS"),
]


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def head(
    *,
    locale: str,
    title: str,
    description: str,
    canonical: str,
    alternates: dict[str, str] | None = None,
    extra: str = "",
) -> str:
    """<head> completo. ``canonical`` e ``alternates`` são caminhos absolutos do site (/..)."""
    url = BASE_URL + canonical
    alt = ""
    if alternates:
        alt = "".join(
            f'  <link rel="alternate" hreflang="{esc(code)}" href="{esc(BASE_URL + path)}">\n'
            for code, path in alternates.items()
        )
    return f"""<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(description)}">
  <link rel="canonical" href="{esc(url)}">
{alt}  <meta name="robots" content="index, follow">
  <meta name="theme-color" content="{THEME_COLOR}">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{esc(url)}">
  <meta property="og:locale" content="{OG_LOCALE[locale]}">
  <meta property="og:site_name" content="runv.club">
  <meta property="og:title" content="{esc(title)}">
  <meta property="og:description" content="{esc(description)}">
  <meta property="og:image" content="{BASE_URL}/assets/og-image.png">
  <meta name="twitter:card" content="summary_large_image">
  <link rel="icon" href="/favicon.svg" type="image/svg+xml">
  <link rel="alternate" type="application/rss+xml" title="runv.club — notícias" href="/news/feed.rss">
  <link rel="stylesheet" href="/assets/style.css">
{extra}</head>"""


def masthead(*, locale: str, current: str | None, stamp: str, other_href: str | None) -> str:
    """Linha de cabeçalho da impressão (host, data/caminho, idioma) + navegação curta."""
    links = []
    for key, href, label in NAV[locale]:
        if key == current:
            links.append(f'<a href="{esc(href)}" aria-current="page">{esc(label)}</a>')
        else:
            links.append(f'<a href="{esc(href)}">{esc(label)}</a>')
    nav = "\n    ".join(links)
    lang = ""
    if other_href:
        lang_other = "en" if locale == "pt" else "pt-BR"
        lang = (
            f'\n    <a href="{esc(other_href)}" hreflang="{lang_other}" lang="{lang_other}" '
            f'class="lang">{esc(OTHER_LABEL[locale])}</a>'
        )
    return f"""<header class="job">
    <span>srv1.runv.club</span>
    <span class="stamp">{esc(stamp)}</span>{lang}
  </header>
  <nav class="menu" aria-label="{'Páginas' if locale == 'pt' else 'Pages'}">
    {nav}
  </nav>"""


def footer(*, locale: str) -> str:
    t = FOOTER[locale]
    badges = "\n      ".join(
        f'<img src="/assets/88x31/{esc(f)}" width="88" height="31" alt="{esc(alt)}">'
        for f, alt in BADGES
    )
    snippet = esc('<a href="https://runv.club/"><img src="https://runv.club/assets/88x31/runv-club.svg" width="88" height="31" alt="runv.club"></a>')
    return f"""<div class="tear" role="separator"></div>
  <footer class="foot">
    <p class="h-card">{t['write']} <a class="u-email" href="mailto:admin@runv.club">admin@runv.club</a> <a class="p-name u-url" href="https://runv.club/" hidden>runv.club</a>
      <br><a href="/news/feed.rss">{t['rss']}</a>  <a href="https://tildeverse.org/">{t['tilde']}</a></p>
    <div class="badges">
      {badges}
    </div>
    <details class="snippet">
      <summary>{t['badge_hint']}</summary>
      <pre><code>{snippet}</code></pre>
    </details>
  </footer>"""


def document(
    *,
    locale: str,
    head_html: str,
    current: str | None,
    stamp: str,
    other_href: str | None,
    body: str,
    main_class: str = "",
    scripts: str = "",
) -> str:
    cls = f' class="{esc(main_class)}"' if main_class else ""
    return f"""<!DOCTYPE html>
<html lang="{LANG_ATTR[locale]}">
{head_html}
<body>
<div class="sheet">
  {masthead(locale=locale, current=current, stamp=stamp, other_href=other_href)}
  <main id="conteudo"{cls}>
{body}
  </main>
  {footer(locale=locale)}
</div>
{scripts}</body>
</html>
"""
