#!/usr/bin/env python3
"""Aplica email-aliases.json no Postfix local (hash). Requer /etc/runv-member-mail.json."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_TOOLS_LIB = _SCRIPT_DIR.parent.parent / "tools" / "lib"
if str(_REPO_TOOLS_LIB) not in sys.path:
    sys.path.insert(0, str(_REPO_TOOLS_LIB))

import runv_mail_sync as ms  # noqa: E402


def require_root(dry_run: bool) -> None:
    if dry_run:
        return
    geteuid = getattr(os, "geteuid", None)
    if geteuid is None or geteuid() != 0:
        print("este script precisa ser executado como root (ou use --dry-run).", file=sys.stderr)
        raise SystemExit(1)


def main() -> int:
    p = argparse.ArgumentParser(
        description="Sincroniza aliases aprovados com Postfix (MTA local, não Mailgun)."
    )
    p.add_argument("--dry-run", action="store_true", help="simular escrita e comandos")
    p.add_argument(
        "--config",
        default="",
        help=f"ficheiro JSON (predefinição: {ms.DEFAULT_CONFIG_PATH})",
    )
    args = p.parse_args()
    require_root(args.dry_run)

    cfg = None
    if args.config.strip():
        cfg = ms.load_config(Path(args.config.strip()))

    return ms.sync_mail(dry_run=args.dry_run, cfg=cfg)


if __name__ == "__main__":
    raise SystemExit(main())
