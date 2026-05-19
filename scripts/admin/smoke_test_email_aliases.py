#!/usr/bin/env python3
"""
Smoke test dos aliases de email runv.club (Linux).

Por defeito usa diretório temporário. Modo --direct chama a biblioteca in-process
(útil em dev/WSL sem sudo). Na VPS use sudo sem --direct para testar os bins.

  sudo python3 scripts/admin/smoke_test_email_aliases.py --user MEMBRO
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from collections.abc import Callable
from contextlib import contextmanager
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BIN_EMAIL = REPO_ROOT / "tools" / "bin" / "runv-email-alias"
BIN_ADMIN = REPO_ROOT / "tools" / "bin" / "runv-admin-email-alias"


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    raise SystemExit(1)


def ok(msg: str) -> None:
    print(f"OK: {msg}")


@contextmanager
def push_env(updates: dict[str, str]):
    old: dict[str, str | None] = {}
    for key, val in updates.items():
        old[key] = os.environ.get(key)
        os.environ[key] = val
    try:
        yield
    finally:
        for key, prev in old.items():
            if prev is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = prev


def run_cmd(
    cmd: list[str],
    *,
    env: dict[str, str],
    as_root: bool = False,
    as_user: str | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    full = list(cmd)
    if as_user:
        full = ["sudo", "-n", "-u", as_user, "-E"] + full
    elif as_root and os.geteuid() != 0:
        full = ["sudo", "-n", "-E"] + full
    proc = subprocess.run(
        full,
        env=env,
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        timeout=60,
    )
    if check and proc.returncode != 0:
        fail(
            f"{' '.join(full)}\nstdout={proc.stdout!r}\nstderr={proc.stderr!r}"
        )
    return proc


def expect_exit(fn: Callable[[], object]) -> bool:
    try:
        fn()
    except SystemExit:
        return True
    return False


def _prepare_smoke_temp_layout(base: Path) -> None:
    """Espelha permissões de produção para subprocess como membro runv-members."""
    import grp

    try:
        member_gid = grp.getgrnam("runv-members").gr_gid
    except KeyError:
        fail("grupo runv-members ausente; execute setup_email_aliases.py primeiro")

    queue = base / "queue"
    aliases = base / "email-aliases.json"
    lock = base / "email-aliases.lock"

    queue.mkdir(parents=True, exist_ok=True)
    for sub in ("approved", "rejected", "cancelled"):
        (queue / sub).mkdir(parents=True, exist_ok=True)

    aliases.write_text("{}\n", encoding="utf-8")
    lock.touch()

    os.chmod(base, 0o755)
    for path in (queue, queue / "approved", queue / "rejected", queue / "cancelled"):
        os.chown(path, 0, member_gid)
        os.chmod(path, 0o2770)
    os.chown(aliases, 0, member_gid)
    os.chmod(aliases, 0o640)
    os.chown(lock, 0, member_gid)
    os.chmod(lock, 0o660)


def main() -> int:
    if sys.platform == "win32":
        print(
            "Este smoke test requer Linux (pwd/grp/fcntl). "
            "Execute na VPS runv ou em WSL.",
            file=sys.stderr,
        )
        return 2

    p = argparse.ArgumentParser(description="Smoke test aliases de email")
    p.add_argument(
        "--production",
        action="store_true",
        help="usar paths em /var/lib/runv (cuidado: altera estado real)",
    )
    p.add_argument(
        "--direct",
        action="store_true",
        help="chamar runv_email_aliases in-process (temp dir; sem testar bins admin root)",
    )
    p.add_argument(
        "--user",
        default="",
        help="username Unix para pedidos",
    )
    args = p.parse_args()
    if args.production and args.direct:
        fail("--production e --direct são incompatíveis")

    username = args.user.strip() or os.environ.get("SUDO_USER", "").strip()
    if not username:
        username = os.environ.get("USER", "").strip()
    if not username:
        fail("defina --user ou execute com USER/SUDO_USER definido")
    if os.geteuid() == 0 and not args.user and not os.environ.get("SUDO_USER"):
        fail("como root directo, use --user MEMBRO (não reservado)")

    sys.path.insert(0, str(REPO_ROOT / "tools" / "lib"))
    import runv_email_aliases as ea  # noqa: E402

    try:
        ea.validate_alias_username(username)
    except SystemExit:
        fail(f"username {username!r} inválido ou reservado para alias")

    if args.production:
        queue = Path("/var/lib/runv/email-alias-queue")
        aliases = Path("/var/lib/runv/email-aliases.json")
        lock = Path("/var/lib/runv/email-aliases.lock")
        tmp_ctx = None
    else:
        tmp_ctx = tempfile.TemporaryDirectory(prefix="runv-email-smoke-")
        base = Path(tmp_ctx.name)
        queue = base / "queue"
        aliases = base / "email-aliases.json"
        lock = base / "email-aliases.lock"
        _prepare_smoke_temp_layout(base)

    env = {
        "RUNV_EMAIL_ALIAS_QUEUE_DIR": str(queue),
        "RUNV_EMAIL_ALIASES_PATH": str(aliases),
        "RUNV_EMAIL_ALIASES_LOCK_PATH": str(lock),
    }

    use_direct = bool(args.direct) or (tmp_ctx is not None and os.geteuid() != 0)
    if use_direct and not args.direct:
        print(
            "aviso: sem root; a usar modo direct (biblioteca). "
            "Na VPS: sudo python3 scripts/admin/smoke_test_email_aliases.py --user MEMBRO",
            file=sys.stderr,
        )

    with push_env(env):
        if use_direct:
            _run_direct(username, queue, aliases)
        else:
            _run_subprocess(env, username, queue, aliases)

    if tmp_ctx is not None:
        tmp_ctx.cleanup()

    print("\nSmoke test aliases de email: PASS")
    return 0


def _run_direct(username: str, queue: Path, aliases: Path) -> None:
    import runv_email_aliases as ea

    for dest in ("foo", "x@runv.club"):
        if not expect_exit(lambda d=dest: ea.validate_destination_email(d)):
            fail(f"validate {dest!r} deveria falhar")
    ok("validações de destino inválido rejeitadas")

    dest_ok = "smoke-alias-test@example.org"
    ea.create_pending_request(username, dest_ok)
    ok("request criado")

    if ea.find_pending_for_user(username) is None:
        fail("pending não encontrado")
    if not expect_exit(lambda: ea.create_pending_request(username, dest_ok)):
        fail("segundo request deveria falhar")
    ok("duplo pending bloqueado")

    entry = ea.approve_pending(username, "smoke-test")
    ok("approve")

    rows = ea.list_active_aliases()
    if not any(r[2] == dest_ok for r in rows):
        fail(f"list_active sem {dest_ok!r}")
    ok("list")

    if ea.get_active_alias(username) is None:
        fail("alias activo ausente após approve")
    ok("status active")

    data = json.loads(aliases.read_text(encoding="utf-8"))
    created_at = data[username].get("created_at")
    if not any((queue / "approved").glob("*.json")):
        fail("nenhum pedido em approved/")
    ok("pedido arquivado em approved/")

    dest2 = "smoke-alias-test2@example.org"
    ea.create_pending_request(username, dest2)
    ea.approve_pending(username, "smoke-test")
    data2 = json.loads(aliases.read_text(encoding="utf-8"))
    if data2[username].get("destination") != dest2:
        fail("destino não actualizado")
    if data2[username].get("created_at") != created_at:
        fail("created_at não preservado")
    ok("alteração de destino com created_at preservado")

    dest3 = "smoke-cancel@example.org"
    ea.create_pending_request(username, dest3)
    if ea.cancel_latest_pending(username) is None:
        fail("cancel falhou")
    ok("cancel")

    dest4 = "smoke-reject@example.org"
    ea.create_pending_request(username, dest4)
    ea.reject_pending(username, "smoke-test", "smoke test")
    if not any((queue / "rejected").glob("*.json")):
        fail("reject não arquivou")
    ok("reject")

    if not expect_exit(lambda: ea.approve_pending("entre", "smoke-test")):
        fail("approve entre deveria falhar")
    ok("username reservado rejeitado no approve")


def _run_subprocess(
    env: dict[str, str],
    username: str,
    queue: Path,
    aliases: Path,
) -> None:
    py = sys.executable
    email_bin = str(BIN_EMAIL) if BIN_EMAIL.is_file() else "runv-email-alias"
    admin_bin = str(BIN_ADMIN) if BIN_ADMIN.is_file() else "runv-admin-email-alias"
    member_user = username if os.geteuid() == 0 else None

    for dest in ("foo", "x@runv.club"):
        proc = run_cmd(
            [py, email_bin, "request", dest],
            env=env,
            as_user=member_user,
            check=False,
        )
        if proc.returncode == 0:
            fail(f"request {dest!r} deveria falhar")
    ok("validações de destino inválido rejeitadas")

    dest_ok = "smoke-alias-test@example.org"
    run_cmd([py, email_bin, "request", dest_ok], env=env, as_user=member_user)
    ok("request criado")

    proc = run_cmd([py, email_bin, "status"], env=env, as_user=member_user)
    if "pending" not in proc.stdout.lower():
        fail(f"status sem pending: {proc.stdout!r}")

    proc2 = run_cmd(
        [py, email_bin, "request", dest_ok],
        env=env,
        as_user=member_user,
        check=False,
    )
    if proc2.returncode == 0:
        fail("segundo request deveria falhar")
    ok("duplo pending bloqueado")

    run_cmd([py, admin_bin, "approve", username], env=env, as_root=True)
    ok("approve")

    proc = run_cmd([py, admin_bin, "list"], env=env, as_root=True)
    if dest_ok not in proc.stdout:
        fail(f"list não mostra destino: {proc.stdout!r}")
    ok("list")

    proc = run_cmd([py, email_bin, "status"], env=env, as_user=member_user)
    if "active" not in proc.stdout.lower():
        fail(f"status sem active: {proc.stdout!r}")
    ok("status active")

    data = json.loads(aliases.read_text(encoding="utf-8"))
    entry = data.get(username)
    if not entry or entry.get("status") != "active":
        fail(f"email-aliases.json inválido: {data!r}")
    if not any((queue / "approved").glob("*.json")):
        fail("nenhum pedido em approved/")
    ok("pedido arquivado em approved/")

    dest2 = "smoke-alias-test2@example.org"
    run_cmd([py, email_bin, "request", dest2], env=env, as_user=member_user)
    run_cmd([py, admin_bin, "approve", username], env=env, as_root=True)
    data2 = json.loads(aliases.read_text(encoding="utf-8"))
    if data2[username].get("destination") != dest2:
        fail("destino não actualizado")
    if data2[username].get("created_at") != entry.get("created_at"):
        fail("created_at não preservado")
    ok("alteração de destino")

    dest3 = "smoke-cancel@example.org"
    run_cmd([py, email_bin, "request", dest3], env=env, as_user=member_user)
    run_cmd([py, email_bin, "cancel"], env=env, as_user=member_user)
    if not any((queue / "cancelled").glob("*.json")):
        fail("cancel não arquivou")
    ok("cancel")

    dest4 = "smoke-reject@example.org"
    run_cmd([py, email_bin, "request", dest4], env=env, as_user=member_user)
    run_cmd(
        [py, admin_bin, "reject", username, "--reason", "smoke test"],
        env=env,
        as_root=True,
    )
    if not any((queue / "rejected").glob("*.json")):
        fail("reject não arquivou")
    ok("reject")

    proc = run_cmd(
        [py, admin_bin, "approve", "entre"],
        env=env,
        as_root=True,
        check=False,
    )
    if proc.returncode == 0:
        fail("approve entre deveria falhar")
    ok("username reservado rejeitado")


if __name__ == "__main__":
    raise SystemExit(main())
