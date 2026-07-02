#!/usr/bin/env python3
"""
Infraestrutura do protocolo **Nex** (porta 1900) e do gateway **kinex** (HTTP → Nex)
para runv.club. Stdlib puro, sem dependências externas.

O que faz (idempotente, com --dry-run):

1. Cria o utilizador de serviço ``runv-nexd`` (system user, sem login).
2. Instala ``nexd.py`` e ``kinex.py`` em ``/usr/local/lib/runv/``.
3. Escreve os units systemd ``runv-nexd.service`` (porta 1900) e, salvo --skip-kinex,
   ``runv-kinex.service`` (127.0.0.1:1971, atrás do Apache em /nex — ver site/genlanding.py).
4. Cria a raiz ``/var/nex`` (755) com um ``index`` que aponta para /users/.
5. Backfill: garante ``~/public_nex`` + ``index`` (modelo) para os membros existentes
   (mesma união users.json + /home e mesma lista de skip que Gopher/Gemini/IRC).
6. Abre a porta 1900/tcp no UFW (se activo) e faz enable --now dos serviços.

**Não** usa bind mounts: o nexd mapeia ``/users/<user>`` directamente para
``/home/<user>/public_nex`` (como o gophernicus faz com public_gopher).

Executar como root no Debian. Ver também scripts/admin/setup_alt_protocols.py (Gopher/Gemini).

Versão 0.01 — runv.club
"""

from __future__ import annotations

import argparse
import logging
import os
import pwd
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Final

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from admin_guard import ensure_admin_cli

# Reutiliza a resolução de utilizadores e a lista de skip do Gopher/Gemini (DRY).
import setup_alt_protocols as alt

VERSION: Final[str] = "0.01"

SERVICE_USER: Final[str] = "runv-nexd"
INSTALL_LIB_DIR: Final[Path] = Path("/usr/local/lib/runv")
NEXD_INSTALL_PATH: Final[Path] = INSTALL_LIB_DIR / "nexd.py"
KINEX_INSTALL_PATH: Final[Path] = INSTALL_LIB_DIR / "kinex.py"

NEX_ROOT: Final[Path] = Path("/var/nex")
DEFAULT_HOMES_ROOT: Final[Path] = Path("/home")
DEFAULT_USERS_JSON: Final[Path] = Path("/var/lib/runv/users.json")
DEFAULT_HOSTNAME: Final[str] = "runv.club"
NEX_PORT: Final[int] = 1900
KINEX_ADDR: Final[str] = "127.0.0.1"
KINEX_PORT: Final[int] = 1971

NEXD_UNIT_PATH: Final[Path] = Path("/etc/systemd/system/runv-nexd.service")
KINEX_UNIT_PATH: Final[Path] = Path("/etc/systemd/system/runv-kinex.service")

USER_NEX_SUBDIR: Final[str] = "public_nex"

DEFAULT_USER_NEX_INDEX: Final[str] = """\
# ~{username} — runv.club (Nex)

Bem-vindo ao meu canto Nex. Nex e o protocolo minimo da small web:
texto puro, uma ligacao, sem barulho.

Edita ~/public_nex/index (e cria mais ficheiros) para tornar este espaco teu.

=> /users/ outros membros
=> / raiz do runv.club
"""

ROOT_NEX_INDEX: Final[str] = """\
# {hostname} — Nex

Bem-vindo ao espaco Nex do runv.club, uma pubnix da small web.
Nex fala texto puro na porta 1900; nada de cabecalhos nem rastreio.

=> /users/ Capsulas dos membros
"""


def setup_logging(verbose: bool) -> logging.Logger:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )
    return logging.getLogger("setup_nex")


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


def ensure_service_user(*, dry_run: bool, log: logging.Logger) -> None:
    try:
        pwd.getpwnam(SERVICE_USER)
        log.info("utilizador de serviço %s já existe", SERVICE_USER)
        return
    except KeyError:
        pass
    if dry_run:
        log.info("[dry-run] criaria utilizador de sistema %s (nologin, sem home)", SERVICE_USER)
        return
    r = run_cmd(
        [
            "adduser",
            "--system",
            "--group",
            "--no-create-home",
            "--shell",
            "/usr/sbin/nologin",
            SERVICE_USER,
        ],
        dry_run=False,
        log=log,
    )
    if r is not None and r.returncode != 0:
        log.error("adduser %s falhou: %s", SERVICE_USER, (r.stderr or r.stdout or "").strip())
    else:
        log.info("utilizador de serviço criado: %s", SERVICE_USER)


def install_daemon_file(src: Path, dest: Path, *, dry_run: bool, log: logging.Logger) -> None:
    if not src.is_file():
        log.error("ficheiro de origem inexistente: %s", src)
        return
    if dry_run:
        log.info("[dry-run] instalaria %s -> %s (0644)", src, dest)
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(dest.parent, 0o755)
    shutil.copy2(src, dest)
    os.chmod(dest, 0o644)
    try:
        os.chown(dest, 0, 0)
    except OSError as e:
        log.warning("chown %s: %s", dest, e)
    log.info("instalado: %s", dest)


def nexd_unit_text() -> str:
    return f"""\
[Unit]
Description=runv.club Nex server (nexd, porta {NEX_PORT})
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User={SERVICE_USER}
Group={SERVICE_USER}
ExecStart=/usr/bin/python3 {NEXD_INSTALL_PATH} --root {NEX_ROOT} --homes-root {DEFAULT_HOMES_ROOT} --hostname {DEFAULT_HOSTNAME} --host 0.0.0.0 --port {NEX_PORT}
Restart=on-failure
RestartSec=2
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=read-only
PrivateTmp=true
ProtectControlGroups=true
ProtectKernelTunables=true
RestrictAddressFamilies=AF_INET AF_INET6

[Install]
WantedBy=multi-user.target
"""


def kinex_unit_text() -> str:
    return f"""\
[Unit]
Description=runv.club Nex→HTML gateway (kinex, {KINEX_ADDR}:{KINEX_PORT})
After=network-online.target runv-nexd.service
Wants=network-online.target

[Service]
Type=simple
User={SERVICE_USER}
Group={SERVICE_USER}
ExecStart=/usr/bin/python3 {KINEX_INSTALL_PATH} --root {NEX_ROOT} --homes-root {DEFAULT_HOMES_ROOT} --hostname {DEFAULT_HOSTNAME} --host {KINEX_ADDR} --port {KINEX_PORT} --base-path /nex
Restart=on-failure
RestartSec=2
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=read-only
PrivateTmp=true
ProtectControlGroups=true
ProtectKernelTunables=true
RestrictAddressFamilies=AF_INET AF_INET6

[Install]
WantedBy=multi-user.target
"""


def write_unit(path: Path, text: str, *, force: bool, dry_run: bool, log: logging.Logger) -> None:
    if dry_run:
        log.info("[dry-run] escreveria unit %s", path)
        return
    if path.is_file() and not force:
        log.info("unit %s já existe (use --force para reescrever)", path)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    os.chmod(path, 0o644)
    log.info("unit escrito: %s", path)


def ensure_nex_root(*, force: bool, dry_run: bool, log: logging.Logger) -> None:
    if dry_run:
        log.info("[dry-run] criaria %s (755) + index raiz", NEX_ROOT)
        return
    NEX_ROOT.mkdir(parents=True, exist_ok=True)
    os.chmod(NEX_ROOT, 0o755)
    try:
        os.chown(NEX_ROOT, 0, 0)
    except OSError as e:
        log.warning("chown %s: %s", NEX_ROOT, e)
    idx = NEX_ROOT / "index"
    if not idx.exists() or force:
        idx.write_text(ROOT_NEX_INDEX.format(hostname=DEFAULT_HOSTNAME), encoding="utf-8")
        os.chmod(idx, 0o644)
        log.info("index raiz Nex: %s", idx)


def ensure_user_public_nex(
    username: str,
    homes_root: Path,
    *,
    force: bool,
    dry_run: bool,
    log: logging.Logger,
) -> None:
    """Garante ~/public_nex + index (modelo). Nunca sobrescreve index existente sem --force."""
    try:
        pw = pwd.getpwnam(username)
    except KeyError:
        log.warning("utilizador %s não existe — salto backfill Nex", username)
        return
    home = Path(pw.pw_dir)
    uid, gid = pw.pw_uid, pw.pw_gid
    ndir = home / USER_NEX_SUBDIR
    nidx = ndir / "index"

    if dry_run:
        log.info("[dry-run] garantiria ~/public_nex + index para %s", username)
        return

    ndir.mkdir(parents=True, exist_ok=True)
    os.chmod(ndir, 0o755)
    os.chown(ndir, uid, gid)

    if not nidx.exists() or force:
        nidx.write_text(DEFAULT_USER_NEX_INDEX.format(username=username), encoding="utf-8")
        os.chmod(nidx, 0o644)
        os.chown(nidx, uid, gid)
        log.info("index Nex: %s", nidx)
    else:
        log.debug("index Nex já existe, mantido: %s", nidx)

    if home.is_dir():
        try:
            import stat as _stat

            cur = _stat.S_IMODE(os.stat(home).st_mode)
            if cur != 0o755:
                os.chmod(home, 0o755)
                log.info("home %s: modo %04o -> 0755", home, cur)
        except OSError as e:
            log.warning("stat/chmod home %s: %s", home, e)


def ufw_maybe_allow(*, dry_run: bool, log: logging.Logger, skip_firewall: bool) -> None:
    if skip_firewall:
        log.info("firewall ignorado (--skip-firewall). Se usar UFW: sudo ufw allow %d/tcp", NEX_PORT)
        return
    r = subprocess.run(["ufw", "status"], capture_output=True, text=True, timeout=30)
    out = (r.stdout or "").lower()
    if r.returncode != 0 or "status: active" not in out:
        log.warning(
            "UFW não activo (ou indisponível). Abra %d/tcp (Nex) manualmente se usar firewall: "
            "sudo ufw allow %d/tcp comment 'nex'",
            NEX_PORT,
            NEX_PORT,
        )
        return
    run_cmd(["ufw", "allow", f"{NEX_PORT}/tcp"], dry_run=dry_run, log=log)
    log.info("UFW: permitido %d/tcp (nex)", NEX_PORT)


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Instala/configura o servidor Nex (nexd) e o gateway kinex.")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--verbose", action="store_true")
    p.add_argument("--force", action="store_true", help="reescreve units e index raiz (backfill: reescreve index de utilizador)")
    p.add_argument("--skip-kinex", action="store_true", help="não instalar o gateway HTTP kinex")
    p.add_argument("--skip-backfill", action="store_true", help="não criar ~/public_nex para membros existentes")
    p.add_argument("--skip-services", action="store_true", help="não fazer daemon-reload/enable/start")
    p.add_argument("--skip-firewall", action="store_true")
    p.add_argument("--users-json", type=Path, default=DEFAULT_USERS_JSON)
    p.add_argument("--homes-root", type=Path, default=DEFAULT_HOMES_ROOT)
    p.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    ensure_admin_cli(script_name=Path(__file__).name, dry_run=bool(args.dry_run))
    log = setup_logging(args.verbose)

    if os.geteuid() != 0 and not args.dry_run:
        log.error("Execute como root (sudo).")
        return 1

    try:
        backfill_users = alt.resolve_backfill_users(args.users_json, args.homes_root, log)
    except (FileNotFoundError, ImportError) as e:
        log.error("%s", e)
        return 1

    ensure_service_user(dry_run=args.dry_run, log=log)

    install_daemon_file(_SCRIPT_DIR / "nexd.py", NEXD_INSTALL_PATH, dry_run=args.dry_run, log=log)
    write_unit(NEXD_UNIT_PATH, nexd_unit_text(), force=args.force, dry_run=args.dry_run, log=log)

    if not args.skip_kinex:
        install_daemon_file(_SCRIPT_DIR / "kinex.py", KINEX_INSTALL_PATH, dry_run=args.dry_run, log=log)
        write_unit(KINEX_UNIT_PATH, kinex_unit_text(), force=args.force, dry_run=args.dry_run, log=log)

    ensure_nex_root(force=args.force, dry_run=args.dry_run, log=log)

    if not args.skip_backfill:
        skip = alt.irc_patch_skip_users(log)
        for u in backfill_users:
            if u in skip:
                log.debug("backfill Nex omitido (skip): %s", u)
                continue
            ensure_user_public_nex(u, args.homes_root, force=args.force, dry_run=args.dry_run, log=log)

    ufw_maybe_allow(dry_run=args.dry_run, log=log, skip_firewall=args.skip_firewall)

    if not args.skip_services:
        run_cmd(["systemctl", "daemon-reload"], dry_run=args.dry_run, log=log)
        run_cmd(["systemctl", "enable", "--now", "runv-nexd.service"], dry_run=args.dry_run, log=log)
        if not args.skip_kinex:
            run_cmd(["systemctl", "enable", "--now", "runv-kinex.service"], dry_run=args.dry_run, log=log)
        if not args.skip_kinex:
            log.info(
                "kinex activo em %s:%d — configure o Apache (/nex) via site/genlanding.py e "
                "active o mod_proxy: sudo a2enmod proxy proxy_http && sudo systemctl reload apache2",
                KINEX_ADDR,
                KINEX_PORT,
            )

    log.info("Concluído. Teste: rex localhost /  (ou: printf '/\\n' | nc localhost %d)", NEX_PORT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
