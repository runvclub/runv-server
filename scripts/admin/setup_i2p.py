#!/usr/bin/env python3
"""
Infraestrutura **I2P** (eepsites por membro) para runv.club. Stdlib puro.

Modelo (opt-in, um site I2P por membro que pedir):

- O router é o **i2pd** (pacote Debian), que corre como serviço ``i2pd``.
- Cada membro activado ganha um **server tunnel HTTP** próprio em
  ``/etc/i2pd/tunnels.conf.d/runv-i2p-<user>.conf`` com o seu próprio ficheiro de
  chaves ``runv-i2p-<user>.dat`` → um **destino** (endereço ``.b32.i2p``) único.
- Todos os túneis apontam para **um único Apache** (``127.0.0.1:7980``) que faz
  *mass virtual hosting* com ``mod_vhost_alias``:
  ``VirtualDocumentRoot /home/%1/public_i2p``. Cada túnel envia
  ``hostoverride = <user>.runv.i2p``, então ``%1`` = ``<user>`` e o Apache serve
  ``~/public_i2p`` do membro certo. Zero config Apache por utilizador.

Ao contrário de Gopher/Gemini/Nex, **não** há porta clearnet de entrada: a
acessibilidade do eepsite vem da própria rede I2P (o i2pd trata do transporte,
inclusive atrás de NAT). Isto torna os eepsites mais privados por natureza.

Comandos:

    setup_i2p.py                      # instala i2pd + Apache mass-vhost (infra base)
    setup_i2p.py --enable pablo willy # activa eepsite(s) por membro
    setup_i2p.py --enable-requested   # activa quem correu «runv-i2p request»
    setup_i2p.py --list-requests      # lista pedidos pendentes (marcador ~/.runv/i2p.request)
    setup_i2p.py --disable pablo      # remove o túnel (mantém chaves e ~/public_i2p)
    setup_i2p.py --list               # mostra membros activos + endereços .b32.i2p
    setup_i2p.py --refresh-addresses  # recalcula .b32 a partir das chaves (sem reload)

Idempotente, com ``--dry-run``. Executar como root no Debian. Ver também
scripts/admin/setup_alt_protocols.py (Gopher/Gemini) e setup_nex.py (Nex).

Versão 0.01 — runv.club
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import logging
import os
import pwd
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Final

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from admin_guard import ensure_admin_cli

# Reutiliza resolução de utilizadores, lista de skip e apt_install do Gopher/Gemini (DRY).
import setup_alt_protocols as alt

VERSION: Final[str] = "0.01"

DEFAULT_USERS_JSON: Final[Path] = Path("/var/lib/runv/users.json")
DEFAULT_HOMES_ROOT: Final[Path] = Path("/home")
DEFAULT_HOSTNAME: Final[str] = "runv.club"

# Apache dedicado ao I2P (mass vhost). Só localhost; os túneis i2pd é que ligam aqui.
I2P_APACHE_ADDR: Final[str] = "127.0.0.1"
I2P_APACHE_PORT: Final[int] = 7980
APACHE_SITE_NAME: Final[str] = "runv-i2p"
APACHE_SITE_CONF: Final[Path] = Path("/etc/apache2/sites-available/runv-i2p.conf")

# i2pd
I2PD_DATADIR: Final[Path] = Path("/var/lib/i2pd")
I2PD_TUNNELS_DIR: Final[Path] = Path("/etc/i2pd/tunnels.conf.d")
I2PD_SERVICE: Final[str] = "i2pd"

# Sufixo do Host interno (não é um nome público; só serve ao vhost do Apache).
HOST_SUFFIX: Final[str] = "runv.i2p"

USER_I2P_SUBDIR: Final[str] = "public_i2p"
REQUEST_MARKER_REL: Final[str] = ".runv/i2p.request"
ADDRESS_STORE: Final[Path] = Path("/var/lib/runv/i2p/addresses.json")
USER_ADDRESS_FILE: Final[str] = ".eepsite-address"

PACKAGES: Final[tuple[str, ...]] = ("i2pd", "apache2")

_USERNAME_RE: Final[re.Pattern[str]] = re.compile(r"^[a-z_][a-z0-9_-]{0,31}$")

DEFAULT_USER_INDEX_HTML: Final[str] = """\
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>~{username} · runv.club (I2P)</title>
<style>
  body {{ font-family: ui-monospace, monospace; max-width: 40rem; margin: 3rem auto;
         padding: 0 1rem; background: #111; color: #eee; line-height: 1.6; }}
  a {{ color: #4ade80; }}
  code {{ color: #93c5fd; }}
</style>
</head>
<body>
<h1>~{username}</h1>
<p>Este é o meu <strong>eepsite</strong> no runv.club, servido pela rede
<strong>I2P</strong> — small web, sem clearnet.</p>
<p>Edito <code>~/public_i2p/</code> por SSH para mudar esta página.</p>
<p><a href="/">/</a> · runv.club</p>
</body>
</html>
"""

APACHE_VHOST_CONF: Final[str] = f"""\
# runv.club — eepsites I2P (mass virtual hosting com mod_vhost_alias).
# Gerido por scripts/admin/setup_i2p.py — não editar à mão.
#
# Cada túnel i2pd envia Host: <user>.{HOST_SUFFIX} (hostoverride), então %1 = <user>
# e o Apache serve /home/<user>/public_i2p. Só escuta em localhost; o acesso vem
# exclusivamente da rede I2P através dos túneis do i2pd.

Listen {I2P_APACHE_ADDR}:{I2P_APACHE_PORT}

<VirtualHost {I2P_APACHE_ADDR}:{I2P_APACHE_PORT}>
    ServerName i2p.{DEFAULT_HOSTNAME}
    UseCanonicalName Off
    LogLevel warn

    VirtualDocumentRoot /home/%1/{USER_I2P_SUBDIR}

    <Directory "/home/*/{USER_I2P_SUBDIR}">
        Options Indexes SymLinksIfOwnerMatch
        AllowOverride None
        Require all granted
    </Directory>
</VirtualHost>
"""


def setup_logging(verbose: bool) -> logging.Logger:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )
    return logging.getLogger("setup_i2p")


def run_cmd(
    cmd: list[str],
    *,
    dry_run: bool,
    log: logging.Logger,
    timeout: int = 300,
) -> subprocess.CompletedProcess[str] | None:
    log.debug("exec: %s", " ".join(cmd))
    if dry_run:
        log.info("[dry-run] %s", " ".join(cmd))
        return None
    return subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=timeout)


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Derivação do endereço .b32.i2p a partir do ficheiro de chaves do i2pd.
#
# O ficheiro .dat começa pela «Destination» (KeysAndCert): 256 bytes de chave
# pública + 128 bytes de chave de assinatura + certificado (tipo[1] + tam[2] +
# payload[tam]). O endereço é base32(sha256(Destination)), minúsculas, sem '='.
# ---------------------------------------------------------------------------
def _destination_length(data: bytes) -> int | None:
    if len(data) < 387:
        return None
    cert_len = int.from_bytes(data[385:387], "big")
    total = 387 + cert_len
    if len(data) < total:
        return None
    return total


def destination_b32(dat_path: Path) -> str | None:
    """Endereço ``<52 chars>.b32.i2p`` do túnel, ou ``None`` se não der para ler/parsear."""
    try:
        data = dat_path.read_bytes()
    except OSError:
        return None
    n = _destination_length(data)
    if n is None:
        return None
    digest = hashlib.sha256(data[:n]).digest()
    b32 = base64.b32encode(digest).decode("ascii").lower().rstrip("=")
    return f"{b32}.b32.i2p"


# ---------------------------------------------------------------------------
# Selecção de membros
# ---------------------------------------------------------------------------
def _service_or_admin(username: str, skip: frozenset[str]) -> bool:
    if username in skip:
        return True
    if username in {"root", "entre", "runv-nexd", "i2pd", "www-data"}:
        return True
    return username.endswith("-admin")


def valid_member(username: str, skip: frozenset[str], log: logging.Logger) -> bool:
    if not _USERNAME_RE.match(username):
        log.error("username inválido: %r", username)
        return False
    if _service_or_admin(username, skip):
        log.warning("%s é conta de serviço/admin — I2P não se aplica", username)
        return False
    try:
        pwd.getpwnam(username)
    except KeyError:
        log.error("utilizador %s não existe no sistema", username)
        return False
    return True


def list_requesters(users: list[str], homes_root: Path, log: logging.Logger) -> list[str]:
    """Membros com o marcador ``~/.runv/i2p.request``."""
    out: list[str] = []
    for u in users:
        try:
            pw = pwd.getpwnam(u)
        except KeyError:
            continue
        if (Path(pw.pw_dir) / REQUEST_MARKER_REL).is_file():
            out.append(u)
    log.debug("pedidos I2P encontrados: %s", ", ".join(out) or "(nenhum)")
    return out


# ---------------------------------------------------------------------------
# Pasta do membro
# ---------------------------------------------------------------------------
def ensure_user_public_i2p(
    username: str,
    *,
    force: bool,
    dry_run: bool,
    log: logging.Logger,
) -> None:
    try:
        pw = pwd.getpwnam(username)
    except KeyError:
        log.warning("utilizador %s não existe — salto ~/public_i2p", username)
        return
    home = Path(pw.pw_dir)
    uid, gid = pw.pw_uid, pw.pw_gid
    idir = home / USER_I2P_SUBDIR
    index = idir / "index.html"

    if dry_run:
        log.info("[dry-run] garantiria ~/public_i2p + index.html para %s", username)
        return

    idir.mkdir(parents=True, exist_ok=True)
    os.chmod(idir, 0o755)
    os.chown(idir, uid, gid)

    if not index.exists() or force:
        index.write_text(DEFAULT_USER_INDEX_HTML.format(username=username), encoding="utf-8")
        os.chmod(index, 0o644)
        os.chown(index, uid, gid)
        log.info("index.html I2P: %s", index)
    else:
        log.debug("index.html I2P já existe, mantido: %s", index)

    # Home atravessável pelo Apache (www-data), como public_html/gopher/gemini/nex.
    try:
        import stat as _stat

        cur = _stat.S_IMODE(os.stat(home).st_mode)
        if cur != 0o755:
            os.chmod(home, 0o755)
            log.info("home %s: modo %04o -> 0755", home, cur)
    except OSError as e:
        log.warning("stat/chmod home %s: %s", home, e)


# ---------------------------------------------------------------------------
# Túnel i2pd por membro
# ---------------------------------------------------------------------------
def tunnel_conf_path(username: str) -> Path:
    return I2PD_TUNNELS_DIR / f"runv-i2p-{username}.conf"


def keys_filename(username: str) -> str:
    return f"runv-i2p-{username}.dat"


def tunnel_conf_text(username: str) -> str:
    return f"""\
# runv.club — eepsite de {username} (gerido por setup_i2p.py; não editar à mão)
[runv-i2p-{username}]
type = http
host = {I2P_APACHE_ADDR}
port = {I2P_APACHE_PORT}
keys = {keys_filename(username)}
hostoverride = {username}.{HOST_SUFFIX}
inbound.length = 3
outbound.length = 3
"""


def write_tunnel_conf(username: str, *, force: bool, dry_run: bool, log: logging.Logger) -> bool:
    """Escreve o .conf do túnel. Devolve True se ficou (novo ou reescrito)."""
    path = tunnel_conf_path(username)
    if dry_run:
        log.info("[dry-run] escreveria túnel i2pd %s", path)
        return True
    if path.is_file() and not force:
        log.info("túnel %s já existe (use --force para reescrever)", path)
        return True
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(tunnel_conf_text(username), encoding="utf-8")
    os.chmod(path, 0o644)
    log.info("túnel i2pd: %s", path)
    return True


def remove_tunnel_conf(username: str, *, dry_run: bool, log: logging.Logger) -> None:
    path = tunnel_conf_path(username)
    if not path.is_file():
        log.info("túnel %s inexistente — nada a remover", path)
        return
    if dry_run:
        log.info("[dry-run] removeria túnel %s", path)
        return
    path.unlink()
    log.info("túnel i2pd removido: %s", path)


def consume_request_marker(username: str, *, dry_run: bool, log: logging.Logger) -> None:
    try:
        pw = pwd.getpwnam(username)
    except KeyError:
        return
    marker = Path(pw.pw_dir) / REQUEST_MARKER_REL
    if not marker.is_file():
        return
    if dry_run:
        log.info("[dry-run] consumiria pedido %s", marker)
        return
    try:
        marker.unlink()
        log.info("pedido consumido: %s", marker)
    except OSError as e:
        log.warning("remover marcador %s: %s", marker, e)


# ---------------------------------------------------------------------------
# Registo de endereços
# ---------------------------------------------------------------------------
def load_address_store(log: logging.Logger) -> dict[str, Any]:
    if not ADDRESS_STORE.is_file():
        return {}
    try:
        data = json.loads(ADDRESS_STORE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError) as e:
        log.warning("ler %s: %s — a começar vazio", ADDRESS_STORE, e)
        return {}


def save_address_store(store: dict[str, Any], *, dry_run: bool, log: logging.Logger) -> None:
    if dry_run:
        log.info("[dry-run] gravaria %s (%d membros)", ADDRESS_STORE, len(store))
        return
    ADDRESS_STORE.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(ADDRESS_STORE.parent, 0o755)
    tmp = ADDRESS_STORE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(store, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.chmod(tmp, 0o644)
    tmp.replace(ADDRESS_STORE)
    log.debug("registo de endereços gravado: %s", ADDRESS_STORE)


def record_address(
    store: dict[str, Any],
    username: str,
    b32: str,
    *,
    dry_run: bool,
    log: logging.Logger,
) -> None:
    entry = store.get(username) or {}
    entry.update(
        {
            "b32": b32,
            "host": f"{username}.{HOST_SUFFIX}",
            "enabled_at": entry.get("enabled_at") or now_iso(),
            "updated_at": now_iso(),
        }
    )
    store[username] = entry
    log.info("%s → %s", username, b32)
    # Cópia de conveniência na home do membro (o .b32 é público, pode partilhar-se).
    try:
        pw = pwd.getpwnam(username)
    except KeyError:
        return
    addr_file = Path(pw.pw_dir) / USER_I2P_SUBDIR / USER_ADDRESS_FILE
    if dry_run:
        log.info("[dry-run] escreveria %s", addr_file)
        return
    try:
        addr_file.parent.mkdir(parents=True, exist_ok=True)
        addr_file.write_text(b32 + "\n", encoding="utf-8")
        os.chmod(addr_file, 0o644)
        os.chown(addr_file, pw.pw_uid, pw.pw_gid)
    except OSError as e:
        log.warning("escrever %s: %s", addr_file, e)


def poll_keys_and_record(
    usernames: list[str],
    store: dict[str, Any],
    datadir: Path,
    *,
    dry_run: bool,
    log: logging.Logger,
    attempts: int = 15,
    delay_s: float = 1.0,
) -> None:
    """Espera o i2pd gerar cada .dat e regista o respectivo .b32."""
    if dry_run:
        for u in usernames:
            log.info("[dry-run] leria %s e registaria .b32 de %s", datadir / keys_filename(u), u)
        return
    pending = set(usernames)
    for i in range(attempts):
        for u in sorted(pending):
            b32 = destination_b32(datadir / keys_filename(u))
            if b32:
                record_address(store, u, b32, dry_run=False, log=log)
                pending.discard(u)
        if not pending:
            break
        log.debug("à espera de chaves i2pd (%d/%d): %s", i + 1, attempts, ", ".join(sorted(pending)))
        time.sleep(delay_s)
    for u in sorted(pending):
        log.warning(
            "chaves de %s ainda não disponíveis em %s — corra «setup_i2p.py --refresh-addresses» "
            "daqui a um minuto",
            u,
            datadir / keys_filename(u),
        )


# ---------------------------------------------------------------------------
# Infra base (i2pd + Apache)
# ---------------------------------------------------------------------------
def ensure_apache_mass_vhost(*, force: bool, dry_run: bool, log: logging.Logger) -> None:
    run_cmd(["a2enmod", "vhost_alias"], dry_run=dry_run, log=log)
    if dry_run:
        log.info("[dry-run] escreveria %s e a2ensite %s", APACHE_SITE_CONF, APACHE_SITE_NAME)
    else:
        if not APACHE_SITE_CONF.is_file() or force:
            APACHE_SITE_CONF.parent.mkdir(parents=True, exist_ok=True)
            APACHE_SITE_CONF.write_text(APACHE_VHOST_CONF, encoding="utf-8")
            os.chmod(APACHE_SITE_CONF, 0o644)
            log.info("vhost Apache I2P: %s", APACHE_SITE_CONF)
        else:
            log.info("%s já existe (use --force para reescrever)", APACHE_SITE_CONF)
    run_cmd(["a2ensite", APACHE_SITE_NAME], dry_run=dry_run, log=log)
    # Valida antes de recarregar; não derruba o Apache por config inválida.
    chk = run_cmd(["apache2ctl", "configtest"], dry_run=dry_run, log=log)
    if chk is not None and chk.returncode != 0:
        log.error("apache2ctl configtest falhou: %s", (chk.stderr or chk.stdout or "").strip())
        return
    run_cmd(["systemctl", "reload", "apache2"], dry_run=dry_run, log=log)


def reload_i2pd(*, dry_run: bool, log: logging.Logger) -> None:
    # reload-or-restart: HUP recarrega os túneis (e gera chaves em falta); se o unit
    # não suportar reload, o systemd reinicia.
    run_cmd(["systemctl", "reload-or-restart", I2PD_SERVICE], dry_run=dry_run, log=log)


def base_infra(*, args: argparse.Namespace, log: logging.Logger) -> bool:
    if not args.skip_install:
        log.info("instalação apt: %s", ", ".join(PACKAGES))
        if not alt.apt_install(PACKAGES, dry_run=args.dry_run, log=log):
            return False
    if not args.dry_run:
        I2PD_TUNNELS_DIR.mkdir(parents=True, exist_ok=True)
    ensure_apache_mass_vhost(force=args.force, dry_run=args.dry_run, log=log)
    run_cmd(["systemctl", "enable", "--now", I2PD_SERVICE], dry_run=args.dry_run, log=log)
    log.info(
        "i2pd activo. Os eepsites não usam porta clearnet de entrada; a rede I2P trata "
        "do transporte (funciona atrás de NAT)."
    )
    return True


# ---------------------------------------------------------------------------
# Acções por membro
# ---------------------------------------------------------------------------
def do_enable(
    usernames: list[str],
    *,
    args: argparse.Namespace,
    skip: frozenset[str],
    log: logging.Logger,
) -> int:
    members = [u for u in usernames if valid_member(u, skip, log)]
    if not members:
        log.error("nenhum membro válido para activar")
        return 1
    for u in members:
        ensure_user_public_i2p(u, force=args.force, dry_run=args.dry_run, log=log)
        write_tunnel_conf(u, force=args.force, dry_run=args.dry_run, log=log)
    reload_i2pd(dry_run=args.dry_run, log=log)
    store = load_address_store(log)
    poll_keys_and_record(members, store, args.i2pd_datadir, dry_run=args.dry_run, log=log)
    save_address_store(store, dry_run=args.dry_run, log=log)
    for u in members:
        consume_request_marker(u, dry_run=args.dry_run, log=log)
    log.info("Activados: %s", ", ".join(members))
    return 0


def enable_member(
    username: str,
    *,
    i2pd_datadir: Path = I2PD_DATADIR,
    force: bool = False,
    log: logging.Logger,
) -> str | None:
    """
    Activa o eepsite de **um** membro e devolve o ``.b32.i2p`` (ou ``None``).

    Ponto de entrada reutilizável (usado por create_runv_user.py). **Não** instala
    pacotes nem escreve o vhost Apache — pressupõe a infra base já instalada
    (``setup_i2p.py`` sem argumentos). Se ``I2PD_TUNNELS_DIR`` não existir, cria só
    ``~/public_i2p`` e devolve ``None`` (o admin ainda tem de correr a infra base).
    """
    ensure_user_public_i2p(username, force=force, dry_run=False, log=log)
    if not I2PD_TUNNELS_DIR.is_dir():
        log.warning(
            "%s inexistente — túnel I2P não criado. Corra scripts/admin/setup_i2p.py "
            "(infra base) e depois --enable %s.",
            I2PD_TUNNELS_DIR,
            username,
        )
        return None
    write_tunnel_conf(username, force=force, dry_run=False, log=log)
    reload_i2pd(dry_run=False, log=log)
    store = load_address_store(log)
    poll_keys_and_record([username], store, i2pd_datadir, dry_run=False, log=log)
    save_address_store(store, dry_run=False, log=log)
    consume_request_marker(username, dry_run=False, log=log)
    return (store.get(username) or {}).get("b32")


def do_disable(
    usernames: list[str],
    *,
    args: argparse.Namespace,
    log: logging.Logger,
) -> int:
    store = load_address_store(log)
    for u in usernames:
        if not _USERNAME_RE.match(u):
            log.error("username inválido: %r", u)
            continue
        remove_tunnel_conf(u, dry_run=args.dry_run, log=log)
        if u in store and not args.dry_run:
            store.pop(u, None)
    reload_i2pd(dry_run=args.dry_run, log=log)
    save_address_store(store, dry_run=args.dry_run, log=log)
    log.info(
        "Desactivados: %s (chaves e ~/public_i2p preservados; o endereço reaparece se reactivar)",
        ", ".join(usernames),
    )
    return 0


def do_refresh(*, args: argparse.Namespace, log: logging.Logger) -> int:
    store = load_address_store(log)
    enabled = sorted(
        p.stem[len("runv-i2p-"):]
        for p in I2PD_TUNNELS_DIR.glob("runv-i2p-*.conf")
    )
    if not enabled:
        log.info("nenhum túnel runv-i2p-*.conf em %s", I2PD_TUNNELS_DIR)
        return 0
    poll_keys_and_record(enabled, store, args.i2pd_datadir, dry_run=args.dry_run, log=log, attempts=1)
    save_address_store(store, dry_run=args.dry_run, log=log)
    return 0


def do_list(log: logging.Logger) -> int:
    store = load_address_store(log)
    if not store:
        print("Nenhum eepsite I2P activo. Active com: setup_i2p.py --enable <user>")
        return 0
    print("Eepsites I2P activos:")
    for u in sorted(store):
        e = store[u]
        print(f"  {u:16s} {e.get('b32', '(sem endereço)')}")
    return 0


def do_list_requests(users: list[str], homes_root: Path, log: logging.Logger) -> int:
    reqs = list_requesters(users, homes_root, log)
    if not reqs:
        print("Sem pedidos pendentes (marcador ~/.runv/i2p.request).")
        return 0
    print("Pedidos I2P pendentes (active com --enable-requested ou --enable <user>):")
    for u in reqs:
        print(f"  {u}")
    return 0


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Instala/gera eepsites I2P (i2pd) por membro no runv.club.")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--verbose", action="store_true")
    p.add_argument("--force", action="store_true", help="reescreve vhost Apache e túneis existentes")
    p.add_argument("--skip-install", action="store_true", help="não instalar i2pd/apache2 via apt")
    p.add_argument("--enable", nargs="+", metavar="USER", help="activar eepsite para o(s) membro(s)")
    p.add_argument("--enable-all", action="store_true", help="activar para todos os membros (exclui serviço/admin)")
    p.add_argument("--enable-requested", action="store_true", help="activar quem tem pedido pendente")
    p.add_argument("--disable", nargs="+", metavar="USER", help="remover o túnel do(s) membro(s)")
    p.add_argument("--list", action="store_true", help="listar eepsites activos + endereços")
    p.add_argument("--list-requests", action="store_true", help="listar pedidos pendentes")
    p.add_argument("--refresh-addresses", action="store_true", help="recalcular .b32 das chaves existentes")
    p.add_argument("--users-json", type=Path, default=DEFAULT_USERS_JSON)
    p.add_argument("--homes-root", type=Path, default=DEFAULT_HOMES_ROOT)
    p.add_argument("--i2pd-datadir", type=Path, default=I2PD_DATADIR)
    p.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    ensure_admin_cli(script_name=Path(__file__).name, dry_run=bool(args.dry_run))
    log = setup_logging(args.verbose)

    if os.geteuid() != 0 and not args.dry_run:
        log.error("Execute como root (sudo).")
        return 1

    # Acções que não precisam de resolver a lista de membros nem root real.
    if args.list:
        return do_list(log)
    if args.refresh_addresses:
        return do_refresh(args=args, log=log)

    try:
        all_users = alt.resolve_backfill_users(args.users_json, args.homes_root, log)
        skip = alt.irc_patch_skip_users(log)
    except (FileNotFoundError, ImportError) as e:
        log.error("%s", e)
        return 1

    if args.list_requests:
        return do_list_requests(all_users, args.homes_root, log)

    # Sempre garante a infra base antes de activar/desactivar.
    if args.enable or args.enable_all or args.enable_requested or not args.disable:
        if not base_infra(args=args, log=log):
            return 1

    targets: list[str] = list(args.enable or [])
    if args.enable_all:
        targets.extend(
            u for u in all_users if not _service_or_admin(u, skip) and _USERNAME_RE.match(u)
        )
    if args.enable_requested:
        targets.extend(list_requesters(all_users, args.homes_root, log))
    targets = sorted(set(targets))

    rc = 0
    if targets:
        rc |= do_enable(targets, args=args, skip=skip, log=log)
    elif args.enable_requested:
        log.info("Nenhum pedido pendente para activar.")

    if args.disable:
        rc |= do_disable(args.disable, args=args, log=log)

    if not targets and not args.disable and not args.enable_requested and not args.enable_all:
        log.info(
            "Infra base pronta. Active membros com: sudo %s --enable <user>  "
            "(ou peça-lhes «runv-i2p request» e corra --enable-requested).",
            Path(__file__).name,
        )
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
