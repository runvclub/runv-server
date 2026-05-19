#!/usr/bin/env python3
"""
Sincroniza aliases aprovados (email-aliases.json) com o MTA local (Postfix hash).

Separado do Mailgun transacional (/etc/runv-email.json). Requer configuração
explícita em /etc/runv-member-mail.json no servidor.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import runv_community as rc

DEFAULT_CONFIG_PATH = Path("/etc/runv-member-mail.json")

try:
    import runv_email_aliases as ea
except ImportError:  # pragma: no cover
    ea = None  # type: ignore[assignment]


def config_path() -> Path:
    raw = os.environ.get("RUNV_MEMBER_MAIL_CONFIG", "").strip()
    return Path(raw) if raw else DEFAULT_CONFIG_PATH


def load_config(path: Path | None = None) -> dict[str, Any]:
    cfg_path = path or config_path()
    if not cfg_path.is_file():
        return {}
    try:
        data = json.loads(cfg_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        rc.friendly_exit(f"config inválida em {cfg_path}: {e}")
    if not isinstance(data, dict):
        rc.friendly_exit(f"config inválida em {cfg_path}: esperado objecto JSON.")
    return data


def is_sync_enabled(cfg: dict[str, Any] | None = None) -> bool:
    data = cfg if cfg is not None else load_config()
    return bool(data.get("enabled"))


def active_forwarding_rows() -> list[tuple[str, str]]:
    if ea is None:
        rc.friendly_exit("módulo runv_email_aliases indisponível.")
    rows: list[tuple[str, str]] = []
    for username, alias, dest in ea.list_active_aliases():
        _ = username
        rows.append((alias.lower(), dest.lower()))
    rows.sort(key=lambda r: r[0])
    return rows


def render_postfix_virtual(rows: list[tuple[str, str]]) -> str:
    lines = [
        "# Gerado por runv — não editar à mão; use runv-admin-email-alias sync",
        "# Formato: alias@dominio    destino@externo",
    ]
    for alias, dest in rows:
        lines.append(f"{alias}\t{dest}")
    lines.append("")
    return "\n".join(lines)


def _run_cmd(cmd: list[str], *, dry_run: bool) -> None:
    if dry_run:
        print(f"[dry-run] {' '.join(cmd)}")
        return
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()
        rc.friendly_exit(f"comando falhou ({' '.join(cmd)}): {err}")


def _atomic_write(path: Path, content: str, *, mode: int, dry_run: bool) -> None:
    if dry_run:
        print(f"[dry-run] escrever {path} ({len(content)} bytes, mode {oct(mode)})")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
    )
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as out:
            out.write(content)
            out.flush()
            os.fsync(out.fileno())
        os.chmod(tmp_path, mode)
        os.replace(tmp_path, path)
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise


def check_postfix_maps_include(target: Path, *, dry_run: bool) -> None:
    proc = subprocess.run(
        ["postconf", "-h", "virtual_alias_maps"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if proc.returncode != 0:
        print(
            "aviso: postconf falhou; confirme manualmente que virtual_alias_maps inclui "
            f"hash:{target}",
            file=sys.stderr,
        )
        return
    maps = (proc.stdout or "").strip()
    needle = f"hash:{target}"
    if needle in maps.replace(" ", ""):
        return
    print(
        f"aviso: virtual_alias_maps actual não referencia {needle}\n"
        f"  actual: {maps or '(vazio)'}\n"
        "  adicione (exemplo):\n"
        f'    postconf -e "virtual_alias_maps = ${{virtual_alias_maps}}, hash:{target}"\n'
        "  ou inclua o ficheiro na configuração existente (MySQL/LDAP/etc.).",
        file=sys.stderr,
    )


def sync_postfix_hash(*, dry_run: bool = False, cfg: dict[str, Any] | None = None) -> int:
    data = cfg if cfg is not None else load_config()
    if not data.get("enabled"):
        rc.friendly_exit(
            f"sincronização desactivada; defina enabled=true em {config_path()}"
        )
    backend = str(data.get("backend", "postfix-hash")).strip().lower()
    if backend != "postfix-hash":
        rc.friendly_exit(f"backend não suportado: {backend!r}")

    target = Path(str(data.get("virtual_alias_file", "/etc/postfix/runv-member-aliases")))
    file_mode = int(str(data.get("file_mode", "0o644")), 8)
    rows = active_forwarding_rows()
    body = render_postfix_virtual(rows)

    _atomic_write(target, body, mode=file_mode, dry_run=dry_run)
    print(f"mapa Postfix: {target} ({len(rows)} alias(es) activo(s))")

    if data.get("check_maps", True):
        check_postfix_maps_include(target, dry_run=dry_run)

    if data.get("run_postmap", True):
        postmap = data.get("postmap_command")
        if isinstance(postmap, list) and postmap:
            cmd = [str(x) for x in postmap]
        else:
            cmd = ["postmap", str(target)]
        _run_cmd(cmd, dry_run=dry_run)

    if data.get("reload_postfix", True):
        reload_cmd = data.get("reload_command")
        if isinstance(reload_cmd, list) and reload_cmd:
            cmd = [str(x) for x in reload_cmd]
        else:
            cmd = ["systemctl", "reload", "postfix"]
        _run_cmd(cmd, dry_run=dry_run)

    return 0


def maybe_sync_after_approve(*, dry_run: bool = False) -> None:
    cfg = load_config()
    if not cfg.get("enabled") or not cfg.get("auto_sync_on_approve"):
        return
    sync_postfix_hash(dry_run=dry_run, cfg=cfg)
