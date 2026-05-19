#!/usr/bin/env python3
"""
Utilitários partilhados pelos comandos comunitários runv.club (stdlib apenas).
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Final

USERNAME_RE: Final[re.Pattern[str]] = re.compile(r"^[a-z][a-z0-9_-]{1,31}$")
MAX_READ_BYTES: Final[int] = 16 * 1024
DEFAULT_USERS_JSON: Final[Path] = Path("/var/lib/runv/users.json")
DEFAULT_HOME_ROOT: Final[Path] = Path("/home")
INSTALLED_LIB_DIR: Final[Path] = Path("/usr/local/share/runv/lib")

PROFILE_DEFAULT: Final[dict[str, Any]] = {
    "display_name": "",
    "bio": "",
    "location": "",
    "links": [],
    "interests": [],
}


def install_bootstrap() -> None:
    """Permite importar este módulo a partir de tools/bin/ ou de /usr/local/bin/."""
    here = Path(__file__).resolve().parent
    candidates: list[Path] = [INSTALLED_LIB_DIR, here]
    try:
        script = Path(sys.argv[0]).resolve()
        if script.parent.name == "bin":
            candidates.insert(0, script.parent.parent / "lib")
    except (IndexError, OSError):
        pass
    for candidate in candidates:
        if (candidate / "runv_community.py").is_file():
            s = str(candidate)
            if s not in sys.path:
                sys.path.insert(0, s)
            return


def friendly_exit(msg: str, code: int = 1) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def validate_username(username: str) -> str:
    u = username.strip()
    if not USERNAME_RE.fullmatch(u):
        friendly_exit(
            "nome de utilizador inválido: use letras minúsculas, dígitos, _ e -; "
            "comece com letra; entre 2 e 32 caracteres."
        )
    return u


def read_text_limited(path: Path, *, max_bytes: int = MAX_READ_BYTES) -> str | None:
    if not path.is_file():
        return None
    try:
        with path.open("rb") as f:
            data = f.read(max_bytes + 1)
        if len(data) > max_bytes:
            data = data[:max_bytes]
        return data.decode("utf-8", errors="replace")
    except OSError:
        return None


def file_has_content(path: Path) -> bool:
    text = read_text_limited(path)
    return text is not None and bool(text.strip())


def parse_profile_json(text: str | None) -> tuple[dict[str, Any] | None, str | None]:
    if text is None:
        return None, None
    raw = text.strip()
    if not raw:
        return None, None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        return None, f"aviso: profile.json inválido ({e.msg})."
    if not isinstance(data, dict):
        return None, "aviso: profile.json deve ser um objeto JSON."
    safe: dict[str, Any] = {}
    for key in ("display_name", "bio", "location"):
        val = data.get(key, "")
        safe[key] = val if isinstance(val, str) else ""
    links = data.get("links", [])
    safe["links"] = [x for x in links if isinstance(x, str)] if isinstance(links, list) else []
    interests = data.get("interests", [])
    safe["interests"] = (
        [x for x in interests if isinstance(x, str)] if isinstance(interests, list) else []
    )
    return safe, None


def home_paths(username: str) -> dict[str, Path]:
    base = DEFAULT_HOME_ROOT / username
    return {
        "home": base,
        "profile": base / ".runv" / "profile.json",
        "plan": base / ".plan",
        "project": base / ".project",
        "public_index": base / "public_html" / "index.html",
    }


def homepage_mtime_iso(path: Path) -> str | None:
    try:
        st = path.stat()
        ts = datetime.fromtimestamp(st.st_mtime, tz=timezone.utc)
        return ts.isoformat().replace("+00:00", "Z")
    except OSError:
        return None


def format_mtime_local(iso_or_path: str | Path | None) -> str | None:
    if iso_or_path is None:
        return None
    if isinstance(iso_or_path, Path):
        iso = homepage_mtime_iso(iso_or_path)
        if iso is None:
            return None
    else:
        iso = iso_or_path
    try:
        if iso.endswith("Z"):
            dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        else:
            dt = datetime.fromisoformat(iso)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        local = dt.astimezone()
        return local.strftime("%Y-%m-%d %H:%M")
    except (ValueError, TypeError):
        return None


def _username_from_item(item: Any) -> str | None:
    if isinstance(item, str) and USERNAME_RE.fullmatch(item):
        return item
    if isinstance(item, dict):
        uname = item.get("username")
        if isinstance(uname, str) and USERNAME_RE.fullmatch(uname):
            return uname
    return None


def _usernames_from_parsed(data: Any) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        if isinstance(data.get("users"), list):
            items = data["users"]
        else:
            items = list(data.keys())
    else:
        return []
    for item in items:
        uname = _username_from_item(item)
        if uname and uname not in seen:
            seen.add(uname)
            found.append(uname)
    return found


def load_member_usernames(
    users_json_path: Path,
    home_root: Path,
) -> tuple[list[str], str | None]:
    warning: str | None = None
    if users_json_path.is_file():
        try:
            raw = users_json_path.read_text(encoding="utf-8").strip()
            if raw:
                parsed = json.loads(raw)
                names = _usernames_from_parsed(parsed)
                if names:
                    return sorted(names, key=str.lower), None
        except (OSError, json.JSONDecodeError):
            warning = (
                f"aviso: não foi possível ler {users_json_path}; "
                "a listar diretórios em /home."
            )
    names_home: list[str] = []
    if home_root.is_dir():
        for entry in home_root.iterdir():
            if entry.is_dir() and USERNAME_RE.fullmatch(entry.name):
                names_home.append(entry.name)
    return sorted(set(names_home), key=str.lower), warning


def profile_json_default_text() -> str:
    return json.dumps(PROFILE_DEFAULT, ensure_ascii=False, indent=2) + "\n"
