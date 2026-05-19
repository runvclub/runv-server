#!/usr/bin/env python3
"""
Lê mysql-virtual-alias-maps.cf e mostra estrutura da tabela (read-only).

Ajuda a preencher /etc/runv-member-mail.json para backend postfix-mysql.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_TOOLS_LIB = _SCRIPT_DIR.parent.parent / "tools" / "lib"
if str(_REPO_TOOLS_LIB) not in sys.path:
    sys.path.insert(0, str(_REPO_TOOLS_LIB))

import runv_mail_sync as ms  # noqa: E402

QUERY_HINT = re.compile(
    r"SELECT\s+[`']?(\w+)[`']?\s+FROM\s+[`']?(\w+)[`']?\s+WHERE\s+[`']?(\w+)[`']?\s*=",
    re.IGNORECASE,
)


def main() -> int:
    p = argparse.ArgumentParser(description="Inspecionar mapa MySQL de aliases Postfix")
    p.add_argument(
        "--map-file",
        default="/etc/postfix/mysql-virtual-alias-maps.cf",
        help="ficheiro .cf do Postfix",
    )
    p.add_argument("--table", default="", help="forçar nome da tabela")
    args = p.parse_args()

    if sys.platform == "win32":
        print("Execute na VPS Linux.", file=sys.stderr)
        return 2

    map_path = Path(args.map_file)
    if not map_path.is_file():
        print(f"ausente: {map_path}", file=sys.stderr)
        return 1

    parsed = ms.parse_postfix_mysql_cf(map_path)
    print(f"=== {map_path} ===")
    for key in ("hosts", "user", "dbname", "query"):
        val = parsed.get(key, "")
        if key == "password":
            continue
        print(f"{key} = {val}")
    print("password = ***")

    query = parsed.get("query", "")
    table = args.table.strip()
    dest_col = ""
    addr_col = ""
    m = QUERY_HINT.search(query.replace("\n", " "))
    if m:
        dest_col, table, addr_col = m.group(1), m.group(2), m.group(3)
        print(f"\ninferido da query: tabela={table!r} col_destino={dest_col!r} col_endereco={addr_col!r}")

    if not table:
        print("\nNão foi possível inferir a tabela; use --table NOME", file=sys.stderr)
        return 1

    sql = f"DESCRIBE `{table}`;"
    print(f"\n=== {sql} ===")
    try:
        out = ms.mysql_exec(parsed, sql, dry_run=False)
        print(out or "(sem saída)")
    except SystemExit as e:
        print(e, file=sys.stderr)
        return 1

    sample = f"SELECT * FROM `{table}` LIMIT 5;"
    print(f"\n=== {sample} ===")
    try:
        print(ms.mysql_exec(parsed, sample, dry_run=False) or "(vazio)")
    except SystemExit:
        print("(amostra indisponível)", file=sys.stderr)

    print(
        "\nSugestão /etc/runv-member-mail.json:\n"
        "{\n"
        '  "enabled": true,\n'
        '  "backend": "postfix-mysql",\n'
        f'  "mysql_map_file": "{map_path}",\n'
        "  \"mysql\": {\n"
        f'    "table": "{table}",\n'
        f'    "address_column": "{addr_col or "address"}",\n'
        f'    "goto_column": "{dest_col or "goto"}",\n'
        '    "active_column": "active",\n'
        '    "active_value": "1"\n'
        "  },\n"
        '  "reload_postfix": true,\n'
        '  "auto_sync_on_approve": true\n'
        "}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
