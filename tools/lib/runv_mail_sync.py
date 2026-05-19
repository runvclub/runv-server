#!/usr/bin/env python3
"""
Sincroniza aliases aprovados (email-aliases.json) com o MTA local.

Backends:
  - postfix-hash: ficheiro + postmap (só se virtual_alias_maps usar hash)
  - postfix-mysql: tabela MySQL já usada por mysql-virtual-alias-maps.cf

Separado do Mailgun transacional (/etc/runv-email.json).
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import runv_community as rc

DEFAULT_CONFIG_PATH = Path("/etc/runv-member-mail.json")
QUERY_HINT = re.compile(
    r"SELECT\s+[`']?(\w+)[`']?\s+FROM\s+[`']?(\w+)[`']?\s+WHERE\s+[`']?(\w+)[`']?\s*=",
    re.IGNORECASE,
)

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


def sql_literal(value: str) -> str:
    return "'" + value.replace("\\", "\\\\").replace("'", "''") + "'"


def parse_postfix_mysql_cf(path: Path) -> dict[str, str]:
    if not path.is_file():
        rc.friendly_exit(f"ficheiro MySQL Postfix ausente: {path}")
    data: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, val = line.split("=", 1)
        data[key.strip().lower()] = val.strip()
    for req in ("user", "password", "hosts", "dbname"):
        if not data.get(req):
            rc.friendly_exit(f"{path} sem campo obrigatório: {req}")
    return data


def mysql_exec(mysql_cfg: dict[str, str], sql: str, *, dry_run: bool) -> str:
    if dry_run:
        print(f"[dry-run] mysql -e {sql}")
        return ""
    cmd = [
        "mysql",
        "-N",
        "-B",
        "-h",
        mysql_cfg["hosts"],
        "-u",
        mysql_cfg["user"],
        mysql_cfg["dbname"],
        "-e",
        sql,
    ]
    env = os.environ.copy()
    env["MYSQL_PWD"] = mysql_cfg["password"]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120, env=env)
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()
        rc.friendly_exit(f"mysql falhou: {err}")
    return (proc.stdout or "").strip()


def infer_mysql_table_from_query(query: str) -> tuple[str, str, str]:
    m = QUERY_HINT.search(query.replace("\n", " "))
    if not m:
        rc.friendly_exit(
            "não foi possível inferir tabela/colunas da query em mysql_map_file; "
            "defina mysql.table, mysql.address_column e mysql.goto_column em runv-member-mail.json"
        )
    dest_col, table, addr_col = m.group(1), m.group(2), m.group(3)
    return table, addr_col, dest_col


def mysql_sync_options(cfg: dict[str, Any]) -> dict[str, str]:
    block = cfg.get("mysql")
    if not isinstance(block, dict):
        block = {}
    map_file = str(
        block.get("map_file")
        or cfg.get("mysql_map_file")
        or "/etc/postfix/mysql-virtual-alias-maps.cf"
    )
    parsed = parse_postfix_mysql_cf(Path(map_file))
    table = str(block.get("table", "")).strip()
    addr_col = str(block.get("address_column", "")).strip()
    goto_col = str(block.get("goto_column", "")).strip()
    if not table or not addr_col or not goto_col:
        inferred_table, inferred_addr, inferred_goto = infer_mysql_table_from_query(
            parsed.get("query", "")
        )
        table = table or inferred_table
        addr_col = addr_col or inferred_addr
        goto_col = goto_col or inferred_goto
    managed_col = str(block.get("managed_column", "")).strip()
    managed_val = str(block.get("managed_value", "runv-email-alias")).strip()
    return {
        "map_file": map_file,
        "parsed": parsed,  # type: ignore[dict-item]
        "table": table,
        "address_column": addr_col,
        "goto_column": goto_col,
        "managed_column": managed_col,
        "managed_value": managed_val,
    }


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
        f"aviso: virtual_alias_maps usa {maps!r} e não hash:{target}.\n"
        "  Para o vosso servidor use backend postfix-mysql, não postfix-hash.",
        file=sys.stderr,
    )


def sync_postfix_hash(*, dry_run: bool = False, cfg: dict[str, Any] | None = None) -> int:
    data = cfg if cfg is not None else load_config()
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


def sync_postfix_mysql(*, dry_run: bool = False, cfg: dict[str, Any] | None = None) -> int:
    data = cfg if cfg is not None else load_config()
    opts = mysql_sync_options(data)
    parsed: dict[str, str] = opts["parsed"]  # type: ignore[assignment]
    table = opts["table"]
    addr_col = opts["address_column"]
    goto_col = opts["goto_column"]
    managed_col = opts["managed_column"]
    managed_val = opts["managed_value"]

    rows = active_forwarding_rows()
    active_addresses = {alias for alias, _ in rows}

    if managed_col:
        in_list = ", ".join(sql_literal(a) for a in sorted(active_addresses)) or "''"
        delete_sql = (
            f"DELETE FROM `{table}` WHERE `{managed_col}` = {sql_literal(managed_val)} "
            f"AND `{addr_col}` NOT IN ({in_list});"
        )
        mysql_exec(parsed, delete_sql, dry_run=dry_run)

    for alias, dest in rows:
        cols = [f"`{addr_col}`", f"`{goto_col}`"]
        vals = [sql_literal(alias), sql_literal(dest)]
        updates = [f"`{goto_col}` = {sql_literal(dest)}"]
        if managed_col:
            cols.append(f"`{managed_col}`")
            vals.append(sql_literal(managed_val))
            updates.append(f"`{managed_col}` = {sql_literal(managed_val)}")
        upsert = (
            f"INSERT INTO `{table}` ({', '.join(cols)}) VALUES ({', '.join(vals)}) "
            f"ON DUPLICATE KEY UPDATE {', '.join(updates)};"
        )
        mysql_exec(parsed, upsert, dry_run=dry_run)
        print(f"  {alias} -> {dest}")

    print(f"MySQL {table}: {len(rows)} alias(es) activo(s) sincronizado(s)")

    if data.get("reload_postfix", True):
        reload_cmd = data.get("reload_command")
        if isinstance(reload_cmd, list) and reload_cmd:
            cmd = [str(x) for x in reload_cmd]
        else:
            cmd = ["systemctl", "reload", "postfix"]
        _run_cmd(cmd, dry_run=dry_run)

    return 0


def sync_mail(*, dry_run: bool = False, cfg: dict[str, Any] | None = None) -> int:
    data = cfg if cfg is not None else load_config()
    if not data.get("enabled"):
        rc.friendly_exit(
            f"sincronização desactivada; defina enabled=true em {config_path()}"
        )
    backend = str(data.get("backend", "postfix-mysql")).strip().lower()
    if backend == "postfix-hash":
        return sync_postfix_hash(dry_run=dry_run, cfg=data)
    if backend == "postfix-mysql":
        return sync_postfix_mysql(dry_run=dry_run, cfg=data)
    rc.friendly_exit(f"backend não suportado: {backend!r}")
    return 1


def maybe_sync_after_approve(*, dry_run: bool = False) -> None:
    cfg = load_config()
    if not cfg.get("enabled") or not cfg.get("auto_sync_on_approve"):
        return
    sync_mail(dry_run=dry_run, cfg=cfg)
