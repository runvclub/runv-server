#!/usr/bin/env python3
"""
Repara artefatos básicos de membros runv sem sobrescrever conteúdo existente.

Uso típico:
  sudo python3 scripts/admin/repair_user.py --user kirihito
  sudo python3 scripts/admin/repair_user.py --all-users --dry-run --verbose

O script é intencionalmente conservador:
- corrige dono/modo da home e dos diretórios públicos esperados;
- cria diretórios ausentes;
- cria index.html, gophermap e index.gmi somente se estiverem ausentes;
- não faz chown recursivo e não toca em /var/vmail, email, Dovecot ou Maildir.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import pwd
import sys
from pathlib import Path
from typing import Final

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from admin_guard import ensure_admin_cli

import create_runv_user

DEFAULT_USERS_JSON: Final[Path] = Path("/var/lib/runv/users.json")
SKIP_USERS: Final[set[str]] = {
    "root",
    "daemon",
    "bin",
    "sys",
    "sync",
    "games",
    "man",
    "lp",
    "mail",
    "news",
    "uucp",
    "proxy",
    "www-data",
    "backup",
    "list",
    "irc",
    "gnats",
    "nobody",
    "systemd-network",
    "systemd-resolve",
    "messagebus",
    "polkitd",
    "sshd",
    "entre",
    "pmurad-admin",
    "vmail",
}


def setup_logging(verbose: bool) -> logging.Logger:
    log = logging.getLogger("repair_user")
    log.setLevel(logging.DEBUG if verbose else logging.INFO)
    log.handlers.clear()
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    log.addHandler(handler)
    return log


def require_root(dry_run: bool, log: logging.Logger) -> None:
    if dry_run:
        return
    if os.geteuid() != 0:
        log.error("execute como root (ou use --dry-run)")
        raise SystemExit(2)


def user_is_member_candidate(pw: pwd.struct_passwd) -> bool:
    if pw.pw_name in SKIP_USERS:
        return False
    if pw.pw_uid < 1000:
        return False
    if not pw.pw_dir.startswith("/home/"):
        return False
    return True


def users_from_metadata(path: Path, log: logging.Logger) -> set[str]:
    if not path.is_file():
        log.debug("metadata ausente: %s", path)
        return set()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        log.warning("não foi possível ler %s: %s", path, e)
        return set()
    if not isinstance(data, list):
        log.warning("%s não contém lista de membros", path)
        return set()
    names: set[str] = set()
    for item in data:
        if not isinstance(item, dict):
            continue
        username = str(item.get("username", "")).strip()
        if username and username not in SKIP_USERS:
            names.add(username)
    return names


def resolve_users(args: argparse.Namespace, log: logging.Logger) -> list[str]:
    if args.user:
        return [args.user.strip()]

    names = users_from_metadata(args.users_json, log)
    for pw in pwd.getpwall():
        if user_is_member_candidate(pw):
            names.add(pw.pw_name)
    return sorted(names)


def chmod_chown(path: Path, mode: int, uid: int, gid: int, *, dry_run: bool, log: logging.Logger) -> bool:
    changed = False
    st = path.stat()
    cur_mode = st.st_mode & 0o777
    if cur_mode != mode:
        changed = True
        if dry_run:
            log.info("[dry-run] chmod %03o %s (era %03o)", mode, path, cur_mode)
        else:
            os.chmod(path, mode)
            log.info("chmod %03o %s", mode, path)
    if st.st_uid != uid or st.st_gid != gid:
        changed = True
        if dry_run:
            log.info("[dry-run] chown %s:%s %s", uid, gid, path)
        else:
            os.chown(path, uid, gid)
            log.info("chown %s:%s %s", uid, gid, path)
    return changed


def ensure_dir(path: Path, mode: int, uid: int, gid: int, *, dry_run: bool, log: logging.Logger) -> bool:
    changed = False
    if path.exists() and not path.is_dir():
        raise RuntimeError(f"{path} existe mas não é diretório")
    if not path.exists():
        changed = True
        if dry_run:
            log.info("[dry-run] mkdir -p %s", path)
        else:
            path.mkdir(parents=True, exist_ok=True)
            log.info("criado diretório %s", path)
    if path.exists():
        changed = chmod_chown(path, mode, uid, gid, dry_run=dry_run, log=log) or changed
    return changed


def ensure_file(
    path: Path,
    body: str,
    mode: int,
    uid: int,
    gid: int,
    *,
    dry_run: bool,
    log: logging.Logger,
) -> bool:
    changed = False
    if path.exists() and not path.is_file():
        raise RuntimeError(f"{path} existe mas não é arquivo regular")
    if not path.exists():
        changed = True
        if dry_run:
            log.info("[dry-run] criaria %s", path)
        else:
            path.write_text(body, encoding="utf-8")
            log.info("criado arquivo %s", path)
    if path.exists():
        changed = chmod_chown(path, mode, uid, gid, dry_run=dry_run, log=log) or changed
    return changed


def repair_one(username: str, *, dry_run: bool, log: logging.Logger) -> tuple[bool, list[str]]:
    warnings: list[str] = []
    pw = pwd.getpwnam(username)
    uid, gid = pw.pw_uid, pw.pw_gid
    home = Path(pw.pw_dir)
    changed = False

    if username in SKIP_USERS:
        warnings.append("usuário reservado ignorado")
        return False, warnings
    if not home.exists():
        raise RuntimeError(f"home ausente: {home}")
    if not home.is_dir():
        raise RuntimeError(f"home não é diretório: {home}")
    if not str(home).startswith("/home/"):
        raise RuntimeError(f"home fora de /home; reparo recusado: {home}")

    changed = chmod_chown(home, 0o755, uid, gid, dry_run=dry_run, log=log) or changed
    changed = ensure_dir(home / ".ssh", 0o700, uid, gid, dry_run=dry_run, log=log) or changed
    auth = home / ".ssh" / "authorized_keys"
    if auth.exists():
        changed = chmod_chown(auth, 0o600, uid, gid, dry_run=dry_run, log=log) or changed
    else:
        warnings.append("authorized_keys ausente; não criado porque falta chave pública")

    changed = ensure_dir(home / "public_html", 0o755, uid, gid, dry_run=dry_run, log=log) or changed
    changed = ensure_file(
        home / "public_html" / "index.html",
        create_runv_user.default_index_html(username),
        0o644,
        uid,
        gid,
        dry_run=dry_run,
        log=log,
    ) or changed

    changed = ensure_dir(home / "public_gopher", 0o755, uid, gid, dry_run=dry_run, log=log) or changed
    changed = ensure_file(
        home / "public_gopher" / "gophermap",
        create_runv_user.default_gophermap_text(username),
        0o644,
        uid,
        gid,
        dry_run=dry_run,
        log=log,
    ) or changed

    changed = ensure_dir(home / "public_gemini", 0o755, uid, gid, dry_run=dry_run, log=log) or changed
    changed = ensure_file(
        home / "public_gemini" / "index.gmi",
        create_runv_user.default_gemini_index_gmi(username),
        0o644,
        uid,
        gid,
        dry_run=dry_run,
        log=log,
    ) or changed

    return changed, warnings


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Repara diretórios e páginas iniciais ausentes de membros runv.",
    )
    target = p.add_mutually_exclusive_group(required=True)
    target.add_argument("--user", metavar="USER", help="repara apenas um usuário")
    target.add_argument("--all-users", action="store_true", help="repara candidatos em users.json e /home")
    p.add_argument("--users-json", type=Path, default=DEFAULT_USERS_JSON)
    p.add_argument("--dry-run", action="store_true", help="mostra sem alterar")
    p.add_argument("--verbose", "-v", action="store_true", help="log detalhado")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    ensure_admin_cli(script_name=Path(__file__).name, dry_run=bool(args.dry_run))
    log = setup_logging(args.verbose)
    require_root(bool(args.dry_run), log)

    users = resolve_users(args, log)
    if not users:
        log.info("nenhum usuário candidato encontrado")
        return 0

    failures = 0
    changed_count = 0
    for username in users:
        log.info("--- reparando %s", username)
        try:
            changed, warnings = repair_one(username, dry_run=bool(args.dry_run), log=log)
        except KeyError:
            log.warning("%s: ausente em passwd; ignorado", username)
            continue
        except Exception as e:
            failures += 1
            log.error("%s: falha: %s", username, e)
            continue
        for warning in warnings:
            log.warning("%s: %s", username, warning)
        if changed:
            changed_count += 1
        else:
            log.info("%s: já estava ok", username)

    print("========== repair_user — resumo ==========")
    print(f"Modo: {'DRY-RUN' if args.dry_run else 'aplicação'}")
    print(f"Usuários processados: {len(users)}")
    print(f"Usuários alterados: {changed_count}")
    print(f"Falhas: {failures}")
    print("==========================================")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
