#!/usr/bin/env python3
"""
Prepara diretórios, permissões e grupo para pedidos de alias de email runv.club.

Não configura Postfix, Dovecot, Mailgun nem DNS.
"""

from __future__ import annotations

import argparse
import logging
import os
import subprocess
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_TOOLS_LIB = _SCRIPT_DIR.parent.parent / "tools" / "lib"
if str(_REPO_TOOLS_LIB) not in sys.path:
    sys.path.insert(0, str(_REPO_TOOLS_LIB))

import runv_community as rc  # noqa: E402

DEFAULT_GROUP = "runv-members"
VAR_LIB_RUNV = Path("/var/lib/runv")
ALIASES_JSON = VAR_LIB_RUNV / "email-aliases.json"
ALIASES_LOCK = VAR_LIB_RUNV / "email-aliases.lock"
QUEUE_DIR = VAR_LIB_RUNV / "email-alias-queue"
USERS_JSON = VAR_LIB_RUNV / "users.json"


def _run(cmd: list[str], *, dry_run: bool, log: logging.Logger) -> subprocess.CompletedProcess[str]:
    log.info("exec: %s", " ".join(cmd))
    if dry_run:
        return subprocess.CompletedProcess(cmd, 0, "", "")
    return subprocess.run(cmd, capture_output=True, text=True, timeout=120)


def require_root(dry_run: bool) -> None:
    if dry_run:
        return
    geteuid = getattr(os, "geteuid", None)
    if geteuid is None or geteuid() != 0:
        print("este script precisa ser executado como root (ou use --dry-run).", file=sys.stderr)
        raise SystemExit(1)


def group_exists(name: str) -> bool:
    try:
        import grp
    except ModuleNotFoundError:
        return False
    try:
        grp.getgrnam(name)
        return True
    except KeyError:
        return False


def ensure_group(name: str, *, dry_run: bool, log: logging.Logger) -> None:
    if dry_run:
        print(f"[dry-run] groupadd {name} (se não existir)")
        return
    if group_exists(name):
        log.info("grupo %s já existe", name)
        return
    r = _run(["groupadd", name], dry_run=dry_run, log=log)
    if dry_run:
        print(f"[dry-run] groupadd {name}")
        return
    if r.returncode != 0:
        err = (r.stderr or r.stdout or "").strip()
        print(f"groupadd {name} falhou: {err}", file=sys.stderr)
        raise SystemExit(1)
    log.info("grupo %s criado", name)


def ensure_dir(path: Path, mode: int, *, dry_run: bool, log: logging.Logger) -> None:
    if dry_run:
        print(f"[dry-run] mkdir {path} mode {oct(mode)}")
        return
    path.mkdir(parents=True, exist_ok=True)
    os.chmod(path, mode)
    log.info("directório %s (%s)", path, oct(mode))


def ensure_file(path: Path, default_content: str, mode: int, *, dry_run: bool, log: logging.Logger) -> None:
    if dry_run:
        action = "criar" if not path.is_file() else "manter"
        print(f"[dry-run] {action} {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.is_file():
        path.write_text(default_content, encoding="utf-8")
        log.info("ficheiro criado: %s", path)
    else:
        raw = path.read_text(encoding="utf-8").strip()
        if not raw:
            path.write_text(default_content, encoding="utf-8")
            log.info("ficheiro inicializado: %s", path)
        else:
            log.info("ficheiro existente preservado: %s", path)
    os.chmod(path, mode)


def chown_path(path: Path, user: str, group: str, *, dry_run: bool, log: logging.Logger) -> None:
    if dry_run:
        print(f"[dry-run] chown {user}:{group} {path}")
        return
    import grp
    import pwd

    try:
        uid = pwd.getpwnam(user).pw_uid
        gid = grp.getgrnam(group).gr_gid
        os.chown(path, uid, gid)
        log.info("chown %s:%s %s", user, group, path)
    except (KeyError, OSError) as e:
        log.warning("não foi possível chown %s: %s", path, e)


def apply_permissions(group: str, *, dry_run: bool, log: logging.Logger) -> None:
    ensure_dir(VAR_LIB_RUNV, 0o755, dry_run=dry_run, log=log)
    if not dry_run:
        try:
            os.chown(VAR_LIB_RUNV, 0, 0)
        except OSError:
            pass

    ensure_file(ALIASES_JSON, "{}\n", 0o640, dry_run=dry_run, log=log)
    ensure_file(ALIASES_LOCK, "", 0o660, dry_run=dry_run, log=log)

    for sub in ("", "approved", "rejected", "cancelled"):
        d = QUEUE_DIR if not sub else QUEUE_DIR / sub
        ensure_dir(d, 0o2770, dry_run=dry_run, log=log)

    if dry_run:
        print(f"[dry-run] chown root:{group} em aliases e fila")
        return

    chown_path(ALIASES_JSON, "root", group, dry_run=False, log=log)
    chown_path(ALIASES_LOCK, "root", group, dry_run=False, log=log)
    for sub in ("", "approved", "rejected", "cancelled"):
        d = QUEUE_DIR if not sub else QUEUE_DIR / sub
        chown_path(d, "root", group, dry_run=False, log=log)


def add_existing_users(group: str, *, dry_run: bool, log: logging.Logger) -> None:
    if not USERS_JSON.is_file():
        print(f"aviso: {USERS_JSON} não encontrado; --add-existing-users ignorado.")
        return
    names, warning = rc.load_member_usernames(USERS_JSON, rc.DEFAULT_HOME_ROOT)
    if warning:
        print(warning)
    if not names:
        print("aviso: nenhum username encontrado em users.json.")
        return
    import pwd

    for username in names:
        if dry_run:
            print(f"[dry-run] usermod -aG {group} {username}")
            continue
        try:
            pwd.getpwnam(username)
        except KeyError:
            print(f"aviso: utilizador Unix {username!r} não existe; ignorado.")
            continue
        r = _run(["usermod", "-aG", group, username], dry_run=False, log=log)
        if r.returncode != 0:
            err = (r.stderr or r.stdout or "").strip()
            print(f"aviso: usermod -aG {group} {username}: {err}")
        else:
            log.info("utilizador %s adicionado ao grupo %s", username, group)


def print_final_instructions(repo_root: Path) -> None:
    tools_dir = repo_root / "tools"
    print()
    print("Setup de aliases de email concluído.\n")
    print("Para instalar comandos:")
    print(f"  cd {tools_dir}")
    print("  sudo python3 tools.py\n")
    print("Para testar como utilizador:")
    print("  runv-email-alias request seu-email@exemplo.com")
    print("  runv-email-alias status\n")
    print("Para admin:")
    print("  sudo runv-admin-email-alias pending")
    print("  sudo runv-admin-email-alias approve USER\n")
    print(
        "Se o servidor não usar o grupo runv-members, pode escolher outro com --group NOME."
    )


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Prepara /var/lib/runv para pedidos de alias de email (sem MTA).",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="mostrar acções sem alterar o sistema",
    )
    p.add_argument(
        "--group",
        default=DEFAULT_GROUP,
        metavar="NOME",
        help=f"grupo Unix com acesso à fila (padrão: {DEFAULT_GROUP})",
    )
    p.add_argument(
        "--add-existing-users",
        action="store_true",
        help="adicionar usernames de /var/lib/runv/users.json ao grupo",
    )
    p.add_argument("-v", "--verbose", action="store_true", help="mais detalhe no log")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )
    log = logging.getLogger("setup_email_aliases")
    require_root(bool(args.dry_run))
    group = args.group.strip()
    if not group:
        print("nome de grupo inválido.", file=sys.stderr)
        return 1

    ensure_group(group, dry_run=bool(args.dry_run), log=log)
    apply_permissions(group, dry_run=bool(args.dry_run), log=log)
    if args.add_existing_users:
        add_existing_users(group, dry_run=bool(args.dry_run), log=log)

    repo_root = _SCRIPT_DIR.parent.parent
    if not args.dry_run:
        print_final_instructions(repo_root)
    else:
        print("\n[dry-run] nenhuma alteração aplicada.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
