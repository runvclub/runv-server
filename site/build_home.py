#!/usr/bin/env python3
"""
build_home — gera a home do runv.club (pt e en) com dados reais do servidor.

A home é a "saída impressa" da máquina: motd (manifesto), ``uname``/status,
``ls -lt`` das páginas dos membros, o passo a passo do ``entre`` e o diário de
mudanças. Tudo o que muda sozinho vem de ficheiros, não do HTML:

- ``data/members.json`` público (gerado por build_directory.py — já filtrado:
  só username, since, path e homepage_mtime). Este script **não** lê users.json.
- ``--homes-root`` (opcional): conta os ficheiros de cada ``~/public_html`` e
  lê a data do ``index.html`` quando o members.json não a trouxer.
- factos da máquina: /etc/os-release, os.cpu_count(), /proc/meminfo, disco.
- ``site/diario.txt``: diário escrito à mão (``AAAA-MM-DD | pt | en``).
- ``site/home.pt.txt`` / ``site/home.en.txt``: o manifesto.

Saída: ``<out-dir>/index.html`` e ``<out-dir>/en/index.html``.

Uso típico no servidor (depois de build_directory.py; genlanding.py já chama):
    python3 site/build_home.py --out-dir /var/www/runv.club/html \\
        --members-json /var/www/runv.club/html/data/members.json --homes-root /home

Local (Windows/dev), com factos fixos:
    python site/build_home.py --facts-json facts.json

Não precisa de root: tudo o que lê é público. Apenas biblioteca padrão.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Final

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import chrome  # noqa: E402

VERSION: Final[str] = "0.1"

# Mesma política de build_directory.py / entre_core.py (ver test_validation_parity).
USERNAME_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[a-z][a-z0-9_-]{1,31}$")

# Brasília não tem horário de verão desde 2019; offset fixo evita depender de tzdata.
BRT: Final[timezone] = timezone(timedelta(hours=-3))

MONTHS_PT: Final[tuple[str, ...]] = ("jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez")
MONTHS_EN: Final[tuple[str, ...]] = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")

MAX_FILES_COUNTED: Final[int] = 5000
DIARY_LIMIT: Final[int] = 8
# index.html mexido até esta distância da criação da conta = ainda é o placeholder.
PLACEHOLDER_WINDOW: Final[timedelta] = timedelta(hours=1)

ASCII_ART: Final[str] = """██████╗ ██╗   ██╗███╗   ██╗██╗   ██╗
██╔══██╗██║   ██║████╗  ██║██║   ██║
██████╔╝██║   ██║██╔██╗ ██║██║   ██║
██╔══██╗╚██╗ ██╔╝██║╚██╗██║╚██╗ ██╔╝
██║  ██║ ╚████╔╝ ██║ ╚████║ ╚████╔╝
╚═╝  ╚═╝  ╚═══╝  ╚═╝  ╚═══╝  ╚═══╝"""

T: Final[dict[str, dict[str, str]]] = {
    "pt": {
        "title": "runv.club — servidor Debian compartilhado",
        "desc": "Pubnix brasileira. Conta shell, public_html servida em HTTP, Gemini, Gopher e Nex, IRC #runv. Entrada via ssh entre@runv.club.",
        "stamp": "{d}",
        "cpus": "{n} vCPUs",
        "ram": "{n} GB RAM",
        "disk": "{n} GB disco",
        "members": "{n} contas ativas. Serviços: HTTP, Gemini, Gopher, Nex, I2P.",
        "members_one": "1 conta ativa. Serviços: HTTP, Gemini, Gopher, Nex, I2P.",
        "irc": "IRC: #runv, irc.tilde.chat:6697/tls (no servidor: chat)",
        "files": "{n} arquivos",
        "files_one": "1 arquivo",
        "untouched": "página padrão",
        "since": "desde {d}",
        "no_members": "nenhuma conta",
        "random": "página aleatória",
        "room": "vagas abertas:",
        "room_link": "solicitar conta",
        "steps_1": 'Gere um par de chaves Ed25519. Comandos para Linux, macOS e Windows em <a href="/junte-se/">/junte-se</a>.',
        "steps_2": "Conecte em <b>ssh entre@runv.club</b> e envie a chave pública pelo formulário do terminal.",
        "steps_3": "A fila é revisada manualmente. Aprovado o pedido, a conta é criada e a confirmação chega por e-mail.",
        "diary_cmd": "tail /var/log/runv/changelog",
        "diary_empty": "sem entradas",
        "after_diary": 'Em andamento: <a href="/now/">/now</a>. Avisos: <a href="/news/">/news</a> e <a href="/news/feed.rss">RSS</a>.',
        "smallweb": (
            'gemini   <a href="gemini://runv.club/">gemini://runv.club/</a>\n'
            'gopher   <a href="gopher://runv.club/">gopher://runv.club/</a>\n'
            'nex      <a href="nex://runv.club/">nex://runv.club/</a>\n'
            'nex/web  <a href="/nex/">/nex/</a>  (no terminal: rex)\n'
            'i2p      <a href="/wiki/i2p-eepsites.html">eepsite por conta</a>\n'
            'feeds    <a href="/recentes/">/recentes</a>  (blogs dos membros)'
        ),
        "join_href": "/junte-se/",
    },
    "en": {
        "title": "runv.club — shared Debian server",
        "desc": "Brazilian pubnix. Shell account, public_html served over HTTP, Gemini, Gopher and Nex, IRC #runv. Sign-up via ssh entre@runv.club.",
        "stamp": "{d}",
        "cpus": "{n} vCPUs",
        "ram": "{n} GB RAM",
        "disk": "{n} GB disk",
        "members": "{n} active accounts. Services: HTTP, Gemini, Gopher, Nex, I2P.",
        "members_one": "1 active account. Services: HTTP, Gemini, Gopher, Nex, I2P.",
        "irc": "IRC: #runv, irc.tilde.chat:6697/tls (on the server: chat)",
        "files": "{n} files",
        "files_one": "1 file",
        "untouched": "default page",
        "since": "since {d}",
        "no_members": "no accounts",
        "random": "random page",
        "room": "sign-ups open:",
        "room_link": "request an account",
        "steps_1": 'Generate an Ed25519 key pair. Commands for Linux, macOS and Windows at <a href="/en/join/">/en/join</a>.',
        "steps_2": "Connect to <b>ssh entre@runv.club</b> and submit your public key through the terminal form (English available).",
        "steps_3": "The queue is reviewed manually. Once approved, the account is created and confirmation is sent by email.",
        "diary_cmd": "tail /var/log/runv/changelog",
        "diary_empty": "no entries",
        "after_diary": 'In progress: <a href="/en/now/">/now</a>. Announcements (Portuguese): <a href="/news/">/news</a> and <a href="/news/feed.rss">RSS</a>.',
        "smallweb": (
            'gemini   <a href="gemini://runv.club/">gemini://runv.club/</a>\n'
            'gopher   <a href="gopher://runv.club/">gopher://runv.club/</a>\n'
            'nex      <a href="nex://runv.club/">nex://runv.club/</a>\n'
            'nex/web  <a href="/nex/">/nex/</a>  (terminal client: rex)\n'
            'i2p      <a href="/en/wiki/i2p-eepsites.html">one eepsite per account</a>\n'
            'feeds    <a href="/recentes/">/recentes</a>  (member blogs)'
        ),
        "join_href": "/en/join/",
    },
}


def eprint(*args: object) -> None:
    print(*args, file=sys.stderr)


def esc(s: str) -> str:
    return html.escape(s, quote=True)


# ---------------------------------------------------------------- dados


@dataclass
class Member:
    username: str
    since: datetime | None
    updated: datetime | None
    files: int | None


def parse_ts(raw: object) -> datetime | None:
    if not isinstance(raw, str) or not raw.strip():
        return None
    s = raw.strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def count_public_files(public_html: Path) -> int | None:
    if not public_html.is_dir():
        return None
    n = 0
    try:
        for _root, _dirs, files in os.walk(public_html, followlinks=False):
            n += len(files)
            if n >= MAX_FILES_COUNTED:
                return MAX_FILES_COUNTED
    except OSError:
        return None
    return n


def index_mtime(public_html: Path) -> datetime | None:
    try:
        st = (public_html / "index.html").stat()
    except OSError:
        return None
    return datetime.fromtimestamp(st.st_mtime, tz=timezone.utc)


def load_members(members_json: Path, homes_root: Path | None) -> list[Member]:
    try:
        raw = json.loads(members_json.read_text(encoding="utf-8"))
    except FileNotFoundError:
        eprint(f"Aviso: {members_json} não existe; a lista de membros sai vazia.")
        return []
    except (OSError, json.JSONDecodeError) as e:
        eprint(f"Aviso: não foi possível ler {members_json}: {e}")
        return []
    if not isinstance(raw, list):
        eprint(f"Aviso: {members_json} não é uma lista JSON.")
        return []
    out: list[Member] = []
    seen: set[str] = set()
    for item in raw:
        if not isinstance(item, dict):
            continue
        u = item.get("username")
        if not isinstance(u, str) or not USERNAME_PATTERN.match(u) or u in seen:
            continue
        seen.add(u)
        since = parse_ts(item.get("since"))
        updated = parse_ts(item.get("homepage_mtime"))
        files: int | None = None
        if homes_root is not None:
            ph = homes_root / u / "public_html"
            files = count_public_files(ph)
            if updated is None:
                updated = index_mtime(ph)
        out.append(Member(username=u, since=since, updated=updated, files=files))
    epoch = datetime.min.replace(tzinfo=timezone.utc)
    out.sort(key=lambda m: (m.updated or m.since or epoch, m.username), reverse=True)
    return out


def read_os_name() -> str | None:
    try:
        text = Path("/etc/os-release").read_text(encoding="utf-8")
    except OSError:
        return None
    for line in text.splitlines():
        if line.startswith("PRETTY_NAME="):
            return line.split("=", 1)[1].strip().strip('"') or None
    return None


def read_mem_gb() -> int | None:
    try:
        text = Path("/proc/meminfo").read_text(encoding="utf-8")
    except OSError:
        return None
    m = re.search(r"^MemTotal:\s+(\d+)\s+kB", text, re.M)
    if not m:
        return None
    return round(int(m.group(1)) / 1024 / 1024)


def read_disk_gb(path: str = "/") -> int | None:
    try:
        # GiB, igual ao "df -h" (que mostra 394G); a RAM também é calculada em GiB.
        return round(shutil.disk_usage(path).total / 1024**3)
    except OSError:
        return None


def machine_facts(facts_json: Path | None) -> dict[str, object]:
    facts: dict[str, object] = {
        "os": read_os_name(),
        "cpus": os.cpu_count(),
        "mem_gb": read_mem_gb(),
        "disk_gb": read_disk_gb(),
    }
    if facts_json is not None:
        try:
            override = json.loads(facts_json.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            eprint(f"Aviso: --facts-json ignorado ({e}).")
        else:
            if isinstance(override, dict):
                facts.update({k: v for k, v in override.items() if k in facts})
    return facts


@dataclass
class DiaryEntry:
    day: datetime
    pt: str
    en: str


def load_diary(path: Path) -> list[DiaryEntry]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as e:
        eprint(f"Aviso: diário {path} não lido ({e}).")
        return []
    out: list[DiaryEntry] = []
    for n, line in enumerate(lines, 1):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        parts = [p.strip() for p in s.split("|")]
        if len(parts) != 3 or not all(parts):
            eprint(f"Aviso: {path}:{n} ignorada (formato: AAAA-MM-DD | pt | en).")
            continue
        try:
            day = datetime.strptime(parts[0], "%Y-%m-%d").replace(tzinfo=BRT)
        except ValueError:
            eprint(f"Aviso: {path}:{n} ignorada (data inválida: {parts[0]!r}).")
            continue
        out.append(DiaryEntry(day=day, pt=parts[1], en=parts[2]))
    out.sort(key=lambda e: e.day, reverse=True)
    return out


# ---------------------------------------------------------------- texto

_LINK_RE = re.compile(r"\[([^\]]+)\]\(((?:https?://|/)[^\s)]*)\)")
_CODE_RE = re.compile(r"`([^`]+)`")
_TILDE_RE = re.compile(r"(?<![\w/~])~([a-z][a-z0-9_-]{1,31})\b")


def inline(text: str) -> str:
    """Escapa e depois aplica o pouco de marcação aceite: [texto](url), `código`, ~usuário."""
    out = esc(text)
    out = _LINK_RE.sub(lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', out)
    out = _CODE_RE.sub(lambda m: f"<code>{m.group(1)}</code>", out)
    out = _TILDE_RE.sub(lambda m: f'<a href="/~{m.group(1)}/">~{m.group(1)}</a>', out)
    return out


def load_manifesto(path: Path) -> list[str]:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as e:
        eprint(f"Aviso: manifesto {path} não lido ({e}).")
        return []
    paras: list[str] = []
    cur: list[str] = []
    for line in raw.splitlines():
        if line.strip().startswith("#"):
            continue
        if line.strip():
            cur.append(line.strip())
        elif cur:
            paras.append(" ".join(cur))
            cur = []
    if cur:
        paras.append(" ".join(cur))
    return paras


def fmt_day(dt: datetime, locale: str) -> str:
    d = dt.astimezone(BRT)
    if locale == "pt":
        return f"{d.day:02d} {MONTHS_PT[d.month - 1]}"
    return f"{MONTHS_EN[d.month - 1]} {d.day:02d}"


def fmt_month_year(dt: datetime, locale: str) -> str:
    d = dt.astimezone(BRT)
    if locale == "pt":
        return f"{MONTHS_PT[d.month - 1]}/{d.year}"
    return f"{MONTHS_EN[d.month - 1]} {d.year}"


def fmt_diary_day(dt: datetime, locale: str) -> str:
    return dt.strftime("%Y-%m-%d")


def fmt_stamp(now: datetime, locale: str) -> str:
    d = now.astimezone(BRT)
    return T[locale]["stamp"].format(d=d.strftime("%Y-%m-%d %H:%M") + " -03")


# ---------------------------------------------------------------- render


def render_manifesto(paras: list[str]) -> str:
    out: list[str] = []
    for i, p in enumerate(paras):
        if p.startswith("— ") or p.startswith("-- "):
            body = inline(p.split(" ", 1)[1]).replace("<a ", '<a class="p-name u-url" ', 1)
            out.append(f'    <p class="sig h-card">— {body}</p>')
        elif i == 0:
            out.append(f'    <p class="lede">{inline(p)}</p>')
        else:
            out.append(f"    <p>{inline(p)}</p>")
    return "\n".join(out)


def render_facts(facts: dict[str, object], n_members: int, locale: str) -> str:
    t = T[locale]
    os_name = facts.get("os") or "Debian"
    hw = []
    for key, label in (("cpus", "cpus"), ("mem_gb", "ram"), ("disk_gb", "disk")):
        v = facts.get(key)
        if isinstance(v, int) and v > 0:
            hw.append(t[label].format(n=v))
    lines = [f"Linux srv1, {os_name}"]
    if hw:
        lines.append(", ".join(hw))
    lines.append(t["members_one"] if n_members == 1 else t["members"].format(n=n_members))
    lines.append(t["irc"])
    return "<pre>" + esc("\n".join(lines)) + "</pre>"


def member_note(m: Member, locale: str) -> str:
    t = T[locale]
    if m.updated and m.since and abs(m.updated - m.since) <= PLACEHOLDER_WINDOW:
        return t["untouched"]
    if m.files is not None and m.files > 0:
        return t["files_one"] if m.files == 1 else t["files"].format(n=m.files)
    if m.since:
        return t["since"].format(d=fmt_month_year(m.since, locale))
    return ""


def render_members(members: list[Member], locale: str) -> str:
    t = T[locale]
    if not members:
        return f'<p class="rem">{esc(t["no_members"])}</p>'
    rows = []
    for m in members:
        when = m.updated or m.since
        day = fmt_day(when, locale) if when else "—"
        iso = when.date().isoformat() if when else ""
        rows.append(
            "      <tr>"
            '<td class="perm">drwxr-xr-x</td>'
            f'<td><time datetime="{iso}">{esc(day)}</time></td>'
            f'<td><a href="/~{esc(m.username)}/">~{esc(m.username)}</a></td>'
            f"<td>{esc(member_note(m, locale))}</td>"
            "</tr>"
        )
    return '<table class="ls">\n' + "\n".join(rows) + "\n    </table>"


def render_diary(entries: list[DiaryEntry], locale: str) -> str:
    t = T[locale]
    if not entries:
        return f'<p class="rem">{esc(t["diary_empty"])}</p>'
    items = []
    for e in entries[:DIARY_LIMIT]:
        text = e.pt if locale == "pt" else e.en
        items.append(
            f'      <li><time datetime="{e.day.date().isoformat()}">{fmt_diary_day(e.day, locale)}</time>'
            f"<span>{inline(text)}</span></li>"
        )
    return '<ul class="log">\n' + "\n".join(items) + "\n    </ul>"


def json_ld(locale: str) -> str:
    data = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": "runv.club",
        "url": "https://runv.club/",
        "inLanguage": chrome.LANG_ATTR[locale],
        "description": T[locale]["desc"],
        "publisher": {
            "@type": "Organization",
            "name": "runv.club",
            "email": "admin@runv.club",
            "parentOrganization": {"@type": "Organization", "name": "Portal IDEA"},
        },
    }
    return '  <script type="application/ld+json">' + json.dumps(data, ensure_ascii=False) + "</script>\n"


def render_home(
    *,
    locale: str,
    members: list[Member],
    facts: dict[str, object],
    diary: list[DiaryEntry],
    manifesto: list[str],
    now: datetime,
) -> str:
    t = T[locale]
    canonical = "/" if locale == "pt" else "/en/"
    head_html = chrome.head(
        locale=locale,
        title=t["title"],
        description=t["desc"],
        canonical=canonical,
        alternates={"pt-BR": "/", "en": "/en/", "x-default": "/"},
        extra=json_ld(locale),
    )
    body = f"""<pre class="art" role="img" aria-label="RUNV">{ASCII_ART}</pre>

    <p class="cmd">cat /etc/motd</p>
{render_manifesto(manifesto)}

    <p class="cmd">uname -a &amp;&amp; runv-status</p>
    {render_facts(facts, len(members), locale)}

    <p class="cmd">ls -lt /home/*/public_html</p>
    {render_members(members, locale)}
    <p><button class="btn" id="aleatorio" type="button" hidden>{esc(t['random'])}</button> <span class="rem">{esc(t['room'])} <a href="{t['join_href']}">{esc(t['room_link'])}</a></span></p>

    <div class="tear" role="separator"></div>

    <h2 class="cmd">ssh entre@runv.club</h2>
    <ol>
      <li>{t['steps_1']}</li>
      <li>{t['steps_2']}</li>
      <li>{t['steps_3']}</li>
    </ol>

    <h2 class="cmd">{esc(t['diary_cmd'])}</h2>
    {render_diary(diary, locale)}
    <p>{t['after_diary']}</p>

    <h2 class="cmd">ls /small-web</h2>
    <pre>{t['smallweb']}</pre>"""
    return chrome.document(
        locale=locale,
        head_html=head_html,
        current="home",
        stamp=fmt_stamp(now, locale),
        other_href="/en/" if locale == "pt" else "/",
        body=body,
        scripts='<script src="/assets/home.js" defer></script>\n',
    )


def write_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    os.replace(tmp, path)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Gera a home do runv.club (pt e en) com dados reais.")
    p.add_argument("--out-dir", type=Path, default=SCRIPT_DIR / "public", help="raiz do site (padrão: site/public)")
    p.add_argument(
        "--members-json",
        type=Path,
        default=None,
        help="members.json público (padrão: <out-dir>/data/members.json)",
    )
    p.add_argument("--homes-root", type=Path, default=None, help="ex. /home: conta ficheiros e lê datas de public_html")
    p.add_argument("--diary", type=Path, default=SCRIPT_DIR / "diario.txt")
    p.add_argument("--manifesto-dir", type=Path, default=SCRIPT_DIR, help="pasta com home.pt.txt e home.en.txt")
    p.add_argument("--facts-json", type=Path, default=None, help="sobrepõe factos da máquina (os, cpus, mem_gb, disk_gb)")
    p.add_argument("--now", default=None, help="data ISO fixa (testes)")
    p.add_argument("--dry-run", action="store_true", help="imprime a home pt em vez de gravar")
    p.add_argument("--version", action="version", version=f"%(prog)s {VERSION} — runv.club")
    args = p.parse_args(argv)

    now = parse_ts(args.now) if args.now else datetime.now(timezone.utc)
    if now is None:
        eprint(f"Erro: --now inválido: {args.now!r}")
        return 2

    members_json = args.members_json or (args.out_dir / "data" / "members.json")
    homes_root = args.homes_root if args.homes_root and args.homes_root.is_dir() else None
    if args.homes_root and homes_root is None:
        eprint(f"Aviso: --homes-root {args.homes_root} não existe; sem contagem de ficheiros.")

    members = load_members(members_json, homes_root)
    facts = machine_facts(args.facts_json)
    diary = load_diary(args.diary)

    for locale in ("pt", "en"):
        manifesto = load_manifesto(args.manifesto_dir / f"home.{locale}.txt")
        page = render_home(
            locale=locale, members=members, facts=facts, diary=diary, manifesto=manifesto, now=now
        )
        target = args.out_dir / ("index.html" if locale == "pt" else "en/index.html")
        if args.dry_run:
            if locale == "pt":
                print(page)
            continue
        write_atomic(target, page)
        print(f"[ok] {target} ({len(members)} membro(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
