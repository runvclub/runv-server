#!/usr/bin/env python3
"""
Remove o modelo antigo de jail SSH runv-jailed de membros existentes.

Desfaz, de forma idempotente, o que ``runv_jail.ensure_runv_jail_for_user`` aplicava:
bind mount em /srv/jail/<user>/home/<user>, linha em /etc/fstab, grupo runv-jailed
e directório /srv/jail/<user>. Também remove o drop-in SSH global da jail.

Execute como root no servidor Debian.
"""

from __future__ import annotations

import argparse
import grp
import logging
import os
import pwd
import subprocess
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from admin_guard import ensure_admin_cli
import runv_jail

SSHD_DROPIN = Path("/etc/ssh/sshd_config.d/90-runv-jailed.conf")


def setup_logging(verbose: bool) -> logging.Logger:
    log = logging.getLogger("remove_runv_jails")
    log.setLevel(logging.DEBUG if verbose else logging.INFO)
    log.handlers.clear()
    h = logging.StreamHandler(sys.stderr)
    h.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    log.addHandler(h)
    return log


def require_root(dry_run: bool, log: logging.Logger) -> None:
    if dry_run:
        return
    if os.geteuid() != 0:
        log.error("execute como root (ou use --dry-run)")
        raise SystemExit(2)


def group_members() -> list[str]:
    try:
        g = grp.getgrnam(runv_jail.RUNV_JAILED_GROUP)
    except KeyError:
        return []
    names = set(g.gr_mem)
    for pw in pwd.getpwall():
        if pw.pw_gid == g.gr_gid:
            names.add(pw.pw_name)
    return sorted(n for n in names if not runv_jail.jail_skip_username(n))


def remove_sshd_dropin(*, dry_run: bool, log: logging.Logger) -> None:
    if not SSHD_DROPIN.exists():
        log.info("drop-in SSH jail ausente: %s", SSHD_DROPIN)
        return
    if dry_run:
        log.info("[dry-run] removeria %s e recarregaria ssh", SSHD_DROPIN)
        return
    old_body = SSHD_DROPIN.read_bytes()
    SSHD_DROPIN.unlink()
    log.info("removido drop-in SSH jail: %s", SSHD_DROPIN)
    test = subprocess.run(["sshd", "-t"], capture_output=True, text=True, timeout=30)
    if test.returncode != 0:
        SSHD_DROPIN.write_bytes(old_body)
        err = (test.stderr or test.stdout or "").strip()
        raise RuntimeError(
            f"sshd -t falhou após remover {SSHD_DROPIN}; ficheiro restaurado: {err}"
        )
    for unit in ("ssh", "sshd"):
        r = subprocess.run(["systemctl", "reload", unit], capture_output=True, text=True, timeout=60)
        if r.returncode == 0:
            log.info("systemctl reload %s concluído", unit)
            return
    log.warning("não foi possível recarregar ssh/sshd automaticamente; recarregue manualmente")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Remove runv-jailed e /srv/jail de membros existentes.")
    p.add_argument("--dry-run", action="store_true", help="mostra sem alterar")
    p.add_argument("--verbose", "-v", action="store_true", help="log detalhado")
    p.add_argument("--user", metavar="USER", help="remove jail apenas deste utilizador")
    p.add_argument(
        "--keep-sshd-dropin",
        action="store_true",
        help="não remover /etc/ssh/sshd_config.d/90-runv-jailed.conf",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    ensure_admin_cli(script_name=Path(__file__).name, dry_run=bool(args.dry_run))
    log = setup_logging(args.verbose)
    require_root(bool(args.dry_run), log)

    users = [args.user.strip()] if args.user else group_members()
    users = [u for u in users if u and not runv_jail.jail_skip_username(u)]
    if not users:
        log.info("nenhum membro em %s", runv_jail.RUNV_JAILED_GROUP)
    for username in users:
        try:
            pw = pwd.getpwnam(username)
        except KeyError:
            log.warning("%s não existe em passwd; ignorado", username)
            continue
        log.info("--- removendo jail de %s", username)
        runv_jail.teardown_runv_jail_for_user(
            username,
            Path(pw.pw_dir),
            log,
            dry_run=bool(args.dry_run),
        )

    if not args.keep_sshd_dropin:
        try:
            remove_sshd_dropin(dry_run=bool(args.dry_run), log=log)
        except RuntimeError as e:
            log.error("%s", e)
            return 1

    log.info("concluído")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
