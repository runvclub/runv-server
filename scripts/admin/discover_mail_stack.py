#!/usr/bin/env python3
"""
Inventário read-only do stack de email no servidor (Postfix, Dovecot, Roundcube, vmail).

Não altera configuração. Use na VPS antes de activar sync_member_email_aliases.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str], *, timeout: int = 30) -> tuple[int, str]:
    if shutil.which(cmd[0]) is None:
        return 127, f"(comando ausente: {cmd[0]})"
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        out = (proc.stdout or "") + (proc.stderr or "")
        return proc.returncode, out.strip()
    except subprocess.TimeoutExpired:
        return 124, "(timeout)"
    except OSError as e:
        return 1, str(e)


def section(title: str) -> None:
    print(f"\n=== {title} ===")


def main() -> int:
    p = argparse.ArgumentParser(description="Inventário do stack de email (read-only)")
    p.parse_args()

    if sys.platform == "win32":
        print("Execute este script na VPS Linux (Debian).", file=sys.stderr)
        return 2

    section("Pacotes Debian (dpkg)")
    code, out = run(
        [
            "dpkg-query",
            "-W",
            "-f=${Package}\t${Status}\n",
            "postfix",
            "dovecot-core",
            "dovecot-imapd",
            "roundcube-core",
            "roundcube",
            "postfix-mysql",
            "postfix-ldap",
        ],
    )
    if code == 127:
        code, out = run(["dpkg", "-l"])
        if code == 0:
            for line in out.splitlines():
                low = line.lower()
                if any(
                    k in low
                    for k in (
                        "postfix",
                        "dovecot",
                        "roundcube",
                        "rspamd",
                        "clamav",
                        "spamassassin",
                    )
                ):
                    print(line)
        else:
            print(out)
    else:
        print(out or "(nenhum pacote listado com esses nomes exactos)")

    section("Serviços (systemctl is-active)")
    for unit in (
        "postfix",
        "dovecot",
        "apache2",
        "nginx",
        "php8.2-fpm",
        "php8.3-fpm",
    ):
        code, out = run(["systemctl", "is-active", unit])
        if code != 127:
            print(f"{unit}: {out}")

    section("Postfix (postconf)")
    for key in (
        "myhostname",
        "mydomain",
        "virtual_mailbox_domains",
        "virtual_mailbox_maps",
        "virtual_alias_maps",
        "relay_domains",
        "transport_maps",
    ):
        code, out = run(["postconf", "-h", key])
        if code == 127:
            print("postconf não instalado")
            break
        print(f"{key} = {out}")

    section("Ficheiros comuns")
    paths = [
        "/etc/postfix/main.cf",
        "/etc/postfix/virtual",
        "/etc/postfix/virtual.db",
        "/etc/postfix/mysql-virtual-alias-maps.cf",
        "/etc/dovecot/dovecot.conf",
        "/var/vmail",
        "/etc/roundcube",
        "/usr/share/roundcube",
        "/var/www/roundcube",
        "/etc/runv-email.json",
        "/etc/runv-member-mail.json",
        "/var/lib/runv/email-aliases.json",
    ]
    for path in paths:
        pth = Path(path)
        if pth.is_dir():
            print(f"{path}/  [dir]")
        elif pth.is_file():
            print(f"{path}  [file]")
        else:
            print(f"{path}  (ausente)")

    section("RunV aliases de membros")
    aliases = Path("/var/lib/runv/email-aliases.json")
    if aliases.is_file():
        print(f"{aliases} existe ({aliases.stat().st_size} bytes)")
    else:
        print(f"{aliases} ausente")

    cfg = Path("/etc/runv-member-mail.json")
    if cfg.is_file():
        print(f"sync MTA configurado: {cfg}")
    else:
        print(
            f"sync MTA não configurado ({cfg} ausente). "
            "Ver email/config/runv-member-mail.example.json"
        )

    section("Mailgun transacional (só leitura de paths)")
    for path in ("/etc/runv-email.json", "/etc/runv-email.secrets.json"):
        pth = Path(path)
        print(f"{path}: {'presente' if pth.is_file() else 'ausente'}")

    print(
        "\nPróximo passo: alinhar virtual_alias_maps com hash:/etc/postfix/runv-member-aliases "
        "e activar /etc/runv-member-mail.json; depois: runv-admin-email-alias sync"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
