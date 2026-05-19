#!/usr/bin/env python3
"""
Utilitários para pedidos e aprovação de aliases de email runv.club (stdlib apenas).
"""

from __future__ import annotations

import json
import os
import re
import secrets
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Final, Literal

import runv_community as rc

DEFAULT_ALIASES_PATH: Final[Path] = Path("/var/lib/runv/email-aliases.json")
DEFAULT_ALIASES_LOCK: Final[Path] = Path("/var/lib/runv/email-aliases.lock")
DEFAULT_QUEUE_DIR: Final[Path] = Path("/var/lib/runv/email-alias-queue")
DEFAULT_ALIAS_DOMAIN: Final[str] = "runv.club"

ALIAS_RESERVED_USERNAMES: Final[frozenset[str]] = frozenset(
    {
        "root",
        "admin",
        "postmaster",
        "abuse",
        "security",
        "support",
        "contato",
        "contact",
        "noreply",
        "no-reply",
        "mailer-daemon",
        "hostmaster",
        "webmaster",
        "entre",
        "join",
        "welcome",
    }
)

DEST_EMAIL_RE: Final[re.Pattern[str]] = re.compile(
    r"^[^@\s\x00\r\n]+@[^@\s\x00\r\n]+\.[^@\s\x00\r\n]+$"
)

ArchiveKind = Literal["approved", "rejected", "cancelled"]


def iso_utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def alias_domain() -> str:
    raw = os.environ.get("RUNV_EMAIL_ALIAS_DOMAIN", "").strip().lower()
    return raw if raw else DEFAULT_ALIAS_DOMAIN


def aliases_paths() -> tuple[Path, Path]:
    aliases = os.environ.get("RUNV_EMAIL_ALIASES_PATH", "").strip()
    lock = os.environ.get("RUNV_EMAIL_ALIASES_LOCK_PATH", "").strip()
    return (
        Path(aliases) if aliases else DEFAULT_ALIASES_PATH,
        Path(lock) if lock else DEFAULT_ALIASES_LOCK,
    )


def queue_paths() -> dict[str, Path]:
    raw = os.environ.get("RUNV_EMAIL_ALIAS_QUEUE_DIR", "").strip()
    base = Path(raw) if raw else DEFAULT_QUEUE_DIR
    return {
        "queue": base,
        "approved": base / "approved",
        "rejected": base / "rejected",
        "cancelled": base / "cancelled",
    }


def validate_alias_username(username: str) -> str:
    u = rc.validate_username(username)
    if u in ALIAS_RESERVED_USERNAMES:
        rc.friendly_exit(f"nome de utilizador reservado para alias de email: {u!r}")
    return u


def validate_destination_email(email: str) -> str:
    addr = email.strip()
    if not addr:
        rc.friendly_exit("email de destino obrigatório.")
    if len(addr) > 254:
        rc.friendly_exit("email de destino demasiado longo (máximo 254 caracteres).")
    if "\x00" in addr or "\n" in addr or "\r" in addr or " " in addr:
        rc.friendly_exit("email de destino inválido.")
    if addr.count("@") != 1:
        rc.friendly_exit("email de destino inválido: deve conter exactamente um @.")
    if not DEST_EMAIL_RE.fullmatch(addr):
        rc.friendly_exit("email de destino inválido.")
    local, domain = addr.rsplit("@", 1)
    if not local or not domain:
        rc.friendly_exit("email de destino inválido.")
    if "." not in domain:
        rc.friendly_exit("email de destino inválido: domínio deve conter pelo menos um ponto.")
    if domain.lower() == alias_domain().lower():
        rc.friendly_exit(
            f"email de destino não pode ser @{alias_domain()} (evita encaminhamento em loop)."
        )
    return addr


def alias_address(username: str) -> str:
    return f"{username}@{alias_domain()}"


def current_username() -> str:
    import pwd

    try:
        name = pwd.getpwuid(os.getuid()).pw_name
    except (KeyError, OSError) as e:
        rc.friendly_exit(f"não foi possível determinar o utilizador: {e}")
    return validate_alias_username(name)


def admin_operator() -> str:
    sudo_user = os.environ.get("SUDO_USER", "").strip()
    if sudo_user:
        return sudo_user
    import pwd

    try:
        return pwd.getpwuid(os.getuid()).pw_name
    except (KeyError, OSError):
        return "root"


def require_root() -> None:
    geteuid = getattr(os, "geteuid", None)
    if geteuid is None or geteuid() != 0:
        rc.friendly_exit("este comando precisa ser executado como root.")


def new_request_id(username: str) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    suffix = secrets.token_hex(3)
    return f"{ts}-{username}-{suffix}"


def _read_json_file(path: Path) -> Any | None:
    if not path.is_file():
        return None
    try:
        raw = path.read_text(encoding="utf-8").strip()
        if not raw:
            return None
        return json.loads(raw)
    except (OSError, json.JSONDecodeError):
        return None


def load_aliases_unlocked(aliases_path: Path) -> dict[str, dict[str, Any]]:
    parsed = _read_json_file(aliases_path)
    if parsed is None:
        return {}
    if not isinstance(parsed, dict):
        rc.friendly_exit(f"formato inválido em {aliases_path}: esperado objecto JSON.")
    out: dict[str, dict[str, Any]] = {}
    for key, val in parsed.items():
        if isinstance(key, str) and isinstance(val, dict):
            out[key] = val
    return out


def load_aliases() -> dict[str, dict[str, Any]]:
    aliases_path, _ = aliases_paths()
    return load_aliases_unlocked(aliases_path)


def save_aliases(data: dict[str, dict[str, Any]]) -> None:
    import fcntl

    aliases_path, lock_path = aliases_paths()
    aliases_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.parent.mkdir(parents=True, exist_ok=True)

    lock_f = open(lock_path, "a+", encoding="utf-8")
    try:
        fcntl.flock(lock_f.fileno(), fcntl.LOCK_EX)
        tmp_fd, tmp_name = tempfile.mkstemp(
            prefix="email-aliases.",
            suffix=".tmp",
            dir=str(aliases_path.parent),
        )
        tmp_path = Path(tmp_name)
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as out:
                json.dump(data, out, indent=2, ensure_ascii=False)
                out.write("\n")
                out.flush()
                os.fsync(out.fileno())
            os.replace(tmp_path, aliases_path)
        except Exception:
            tmp_path.unlink(missing_ok=True)
            raise
    finally:
        fcntl.flock(lock_f.fileno(), fcntl.LOCK_UN)
        lock_f.close()


def get_active_alias(username: str) -> dict[str, Any] | None:
    entry = load_aliases().get(username)
    if not entry or entry.get("status") != "active":
        return None
    return entry


def _queue_request_file(request_id: str) -> Path:
    return queue_paths()["queue"] / f"{request_id}.json"


def _parse_request(path: Path) -> dict[str, Any] | None:
    data = _read_json_file(path)
    if not isinstance(data, dict):
        return None
    return data


def iter_pending_requests() -> list[dict[str, Any]]:
    qdir = queue_paths()["queue"]
    if not qdir.is_dir():
        return []
    pending: list[dict[str, Any]] = []
    for path in sorted(qdir.glob("*.json")):
        if not path.is_file():
            continue
        req = _parse_request(path)
        if req and req.get("status") == "pending":
            pending.append({**req, "_path": str(path)})
    pending.sort(key=lambda r: str(r.get("created_at", "")))
    return pending


def find_pending_for_user(username: str) -> dict[str, Any] | None:
    for req in iter_pending_requests():
        if req.get("username") == username:
            return req
    return None


def find_latest_pending_for_user(username: str) -> tuple[dict[str, Any], Path] | None:
    matches: list[tuple[dict[str, Any], Path]] = []
    qdir = queue_paths()["queue"]
    if not qdir.is_dir():
        return None
    for path in qdir.glob("*.json"):
        if not path.is_file():
            continue
        req = _parse_request(path)
        if req and req.get("username") == username and req.get("status") == "pending":
            matches.append((req, path))
    if not matches:
        return None

    def sort_key(item: tuple[dict[str, Any], Path]) -> str:
        req, path = item
        created = req.get("created_at")
        if isinstance(created, str) and created:
            return created
        try:
            return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
        except OSError:
            return ""

    matches.sort(key=sort_key)
    req, path = matches[-1]
    return req, path


def create_pending_request(username: str, destination: str) -> dict[str, Any]:
    paths = queue_paths()
    try:
        paths["queue"].mkdir(parents=True, exist_ok=True)
    except OSError as e:
        rc.friendly_exit(f"não foi possível criar o diretório da fila: {e}")

    if find_pending_for_user(username) is not None:
        rc.friendly_exit(
            "Já existe pedido pendente.\n"
            "Veja o status com:\n"
            "  runv-email-alias status\n\n"
            "Para cancelar:\n"
            "  runv-email-alias cancel"
        )

    request_id = new_request_id(username)
    alias = alias_address(username)
    payload: dict[str, Any] = {
        "request_id": request_id,
        "username": username,
        "alias": alias,
        "destination": destination,
        "status": "pending",
        "created_at": iso_utc_now(),
    }
    dest_path = _queue_request_file(request_id)
    try:
        fd = os.open(
            dest_path,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            0o664,
        )
    except FileExistsError:
        rc.friendly_exit("conflito ao criar pedido; tente novamente.")
    except PermissionError:
        rc.friendly_exit(
            f"sem permissão para criar pedido em {paths['queue']}\n"
            "peça ao admin para executar:\n"
            "  sudo python3 scripts/admin/setup_email_aliases.py"
        )
    except OSError as e:
        rc.friendly_exit(f"erro ao criar pedido: {e}")

    try:
        with os.fdopen(fd, "w", encoding="utf-8") as out:
            json.dump(payload, out, indent=2, ensure_ascii=False)
            out.write("\n")
    except OSError as e:
        dest_path.unlink(missing_ok=True)
        rc.friendly_exit(f"erro ao gravar pedido: {e}")
    return payload


def archive_request(
    path: Path,
    payload: dict[str, Any],
    kind: ArchiveKind,
) -> Path:
    paths = queue_paths()
    dest_dir = paths[kind]
    dest_dir.mkdir(parents=True, exist_ok=True)
    request_id = payload.get("request_id")
    if not isinstance(request_id, str) or not request_id:
        request_id = path.stem
    dest = dest_dir / f"{request_id}.json"
    if dest.exists():
        dest = dest_dir / f"{request_id}-{secrets.token_hex(2)}.json"
    try:
        path.replace(dest)
    except OSError:
        dest.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        path.unlink(missing_ok=True)
    return dest


def cancel_latest_pending(username: str) -> dict[str, Any] | None:
    found = find_latest_pending_for_user(username)
    if found is None:
        return None
    req, path = found
    req["status"] = "cancelled"
    req["cancelled_at"] = iso_utc_now()
    archive_request(path, req, "cancelled")
    return req


def approve_pending(username: str, operator: str) -> dict[str, Any]:
    validate_alias_username(username)
    found = find_latest_pending_for_user(username)
    if found is None:
        rc.friendly_exit(f"nenhum pedido pendente para o utilizador {username!r}.")
    req, path = found
    destination = req.get("destination")
    if not isinstance(destination, str):
        rc.friendly_exit("pedido pendente sem email de destino válido.")
    destination = validate_destination_email(destination)

    aliases_path, _ = aliases_paths()
    import fcntl

    aliases_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = aliases_paths()[1]
    lock_path.parent.mkdir(parents=True, exist_ok=True)

    lock_f = open(lock_path, "a+", encoding="utf-8")
    try:
        fcntl.flock(lock_f.fileno(), fcntl.LOCK_EX)
        data = load_aliases_unlocked(aliases_path)
        now = iso_utc_now()
        alias = alias_address(username)
        existing = data.get(username)
        created_at = now
        if isinstance(existing, dict) and isinstance(existing.get("created_at"), str):
            created_at = existing["created_at"]
        data[username] = {
            "username": username,
            "alias": alias,
            "destination": destination,
            "status": "active",
            "created_at": created_at,
            "updated_at": now,
            "approved_by": operator,
        }
        tmp_fd, tmp_name = tempfile.mkstemp(
            prefix="email-aliases.",
            suffix=".tmp",
            dir=str(aliases_path.parent),
        )
        tmp_path = Path(tmp_name)
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as out:
                json.dump(data, out, indent=2, ensure_ascii=False)
                out.write("\n")
                out.flush()
                os.fsync(out.fileno())
            os.replace(tmp_path, aliases_path)
        except Exception:
            tmp_path.unlink(missing_ok=True)
            raise
    finally:
        fcntl.flock(lock_f.fileno(), fcntl.LOCK_UN)
        lock_f.close()

    req["status"] = "approved"
    req["approved_at"] = iso_utc_now()
    req["approved_by"] = operator
    archive_request(path, req, "approved")
    return data[username]


def reject_pending(username: str, operator: str, reason: str) -> dict[str, Any]:
    validate_alias_username(username)
    found = find_latest_pending_for_user(username)
    if found is None:
        rc.friendly_exit(f"nenhum pedido pendente para o utilizador {username!r}.")
    req, path = found
    req["status"] = "rejected"
    req["rejected_at"] = iso_utc_now()
    req["rejected_by"] = operator
    req["reason"] = reason
    archive_request(path, req, "rejected")
    return req


def list_active_aliases() -> list[tuple[str, str, str]]:
    data = load_aliases()
    rows: list[tuple[str, str, str]] = []
    for username in sorted(data.keys(), key=str.lower):
        entry = data[username]
        if entry.get("status") != "active":
            continue
        alias = entry.get("alias")
        dest = entry.get("destination")
        if isinstance(alias, str) and isinstance(dest, str):
            rows.append((username, alias, dest))
    return rows
