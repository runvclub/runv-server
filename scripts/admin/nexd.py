#!/usr/bin/env python3
"""
nexd — servidor do protocolo **Nex** para runv.club (stdlib puro, sem dependências).

Nex é o protocolo mínimo da Nightfall City: o cliente abre TCP na porta 1900,
envia **uma linha** (o selector/caminho) terminada por LF, e o servidor devolve o
conteúdo cru e fecha a ligação. Não há linha de estado nem cabeçalhos — é a versão
mais simples possível de Gopher/Gemini. Links são linhas ``=> caminho Nome``.

Modelo runv (espelha o gophernicus, **sem** bind mounts):

- Raiz do sistema em ``/var/nex`` (índice raiz, páginas globais).
- ``/users/<user>/...`` é mapeado directamente para ``/home/<user>/public_nex/...``
  (a home é 755 e ``public_nex`` 755, servidos com ``index``/``644`` — o mesmo
  contrato de permissões que Gopher e Gemini já garantem em create_runv_user.py).
- ``/users/`` gera a lista de membros com ``public_nex`` (uid >= 1000).

Segurança: o selector é sempre saneado (rejeita ``..``, ``.`` e componentes
vazios) e o caminho final é validado com ``realpath`` contra a raiz permitida —
nunca serve nada fora de ``/var/nex`` ou de ``/home/<user>/public_nex``.

Correr como serviço (utilizador sem privilégios) via systemd; ver scripts/admin/setup_nex.py.

Versão 0.01 — runv.club
"""

from __future__ import annotations

import argparse
import logging
import os
import socket
import socketserver
import sys
from pathlib import Path
from typing import Final

try:
    import pwd
except ImportError:  # não-Unix (ex.: Windows): permite testar as funções puras
    pwd = None  # type: ignore[assignment]

VERSION: Final[str] = "0.01"

DEFAULT_ROOT: Final[Path] = Path("/var/nex")
DEFAULT_HOMES_ROOT: Final[Path] = Path("/home")
DEFAULT_HOST: Final[str] = "0.0.0.0"
DEFAULT_PORT: Final[int] = 1900
DEFAULT_USER_SUBDIR: Final[str] = "public_nex"
MIN_UID_USER: Final[int] = 1000
MAX_SELECTOR_BYTES: Final[int] = 4096
READ_TIMEOUT_S: Final[float] = 20.0

# Contas de sistema/serviço que nunca aparecem na lista de membros /users/.
SKIP_USERS: Final[frozenset[str]] = frozenset(
    {
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
        "_apt",
        "nobody",
        "admin",
        "postmaster",
        "entre",
        "pmurad-admin",
    }
)


class NexConfig:
    """Configuração imutável partilhada pelos handlers (nexd e kinex)."""

    def __init__(
        self,
        *,
        root: Path = DEFAULT_ROOT,
        homes_root: Path = DEFAULT_HOMES_ROOT,
        hostname: str = "runv.club",
    ) -> None:
        self.root = root.resolve()
        self.homes_root = homes_root.resolve()
        self.hostname = hostname


# ---------------------------------------------------------------------------
# Saneamento de selector e resolução de caminho (funções puras — testáveis)
# ---------------------------------------------------------------------------
def sanitize_selector(raw: str) -> str:
    """
    Normaliza o selector recebido do cliente.

    - Corta CR/LF e espaços nas pontas.
    - Garante que começa por ``/``.
    - Rejeita (ValueError) qualquer componente ``..`` — proteção anti-traversal.
    Componentes ``.`` e vazios são simplesmente removidos.
    """
    s = raw.replace("\r", "").replace("\n", "").strip()
    if not s:
        return "/"
    if not s.startswith("/"):
        s = "/" + s
    trailing_slash = s.endswith("/")
    parts: list[str] = []
    for comp in s.split("/"):
        if comp in ("", "."):
            continue
        if comp == "..":
            raise ValueError("componente '..' não permitido no selector")
        parts.append(comp)
    norm = "/" + "/".join(parts)
    if trailing_slash and not norm.endswith("/"):
        norm += "/"
    return norm


def _safe_join(base: Path, rel_parts: list[str]) -> Path | None:
    """
    Junta ``rel_parts`` sob ``base`` e confirma, via realpath, que o resultado
    permanece dentro de ``base``. Devolve None se escapar (symlink malicioso, etc.).
    """
    base_res = base.resolve()
    candidate = base_res
    for part in rel_parts:
        candidate = candidate / part
    try:
        resolved = candidate.resolve(strict=False)
    except OSError:
        return None
    try:
        resolved.relative_to(base_res)
    except ValueError:
        return None
    return resolved


def resolve_selector_path(cfg: NexConfig, selector: str) -> tuple[str, Path | None, str | None]:
    """
    Traduz um selector saneado num alvo do sistema de ficheiros.

    Devolve ``(kind, path, username)`` onde ``kind`` ∈
    {``"root"``, ``"users_index"``, ``"user"``}:

    - ``root``        → ``path`` sob ``/var/nex``.
    - ``users_index`` → ``path`` é None (lista de membros gerada dinamicamente).
    - ``user``        → ``path`` sob ``/home/<username>/public_nex`` (ou None se inválido).
    """
    parts = [p for p in selector.split("/") if p]
    if parts and parts[0] == "users":
        rest = parts[1:]
        if not rest:
            return ("users_index", None, None)
        username = rest[0]
        if not _valid_username(username):
            return ("user", None, username)
        user_base = cfg.homes_root / username / DEFAULT_USER_SUBDIR
        path = _safe_join(user_base, rest[1:])
        return ("user", path, username)
    path = _safe_join(cfg.root, parts)
    return ("root", path, None)


def _valid_username(name: str) -> bool:
    if not name or len(name) > 32:
        return False
    if name in SKIP_USERS:
        return False
    return all(c.islower() or c.isdigit() or c in "_-" for c in name) and name[0].islower()


def list_member_usernames(cfg: NexConfig) -> list[str]:
    """Membros com ``~/public_nex`` (uid >= 1000, fora de SKIP_USERS)."""
    names: list[str] = []
    if pwd is None:
        return names
    try:
        entries = sorted(p.name for p in cfg.homes_root.iterdir() if p.is_dir())
    except OSError:
        return names
    for name in entries:
        if not _valid_username(name):
            continue
        try:
            pw = pwd.getpwnam(name)
        except KeyError:
            continue
        if pw.pw_uid < MIN_UID_USER:
            continue
        if (cfg.homes_root / name / DEFAULT_USER_SUBDIR).is_dir():
            names.append(name)
    return names


# ---------------------------------------------------------------------------
# Geração de conteúdo Nex
# ---------------------------------------------------------------------------
def render_members_index(cfg: NexConfig) -> bytes:
    lines = [
        f"# {cfg.hostname} — membros no Nex",
        "",
        "Cápsulas Nex dos membros do runv.club:",
        "",
    ]
    members = list_member_usernames(cfg)
    if members:
        for name in members:
            lines.append(f"=> /users/{name}/ ~{name}")
    else:
        lines.append("(ainda sem cápsulas Nex publicadas)")
    lines.append("")
    lines.append("=> / voltar à raiz")
    lines.append("")
    return ("\n".join(lines)).encode("utf-8")


def render_directory_listing(dir_path: Path, selector: str) -> bytes:
    """
    Lista um directório em formato Nex. Prepende ``.header`` se existir.
    Ordena por nome; directórios primeiro, com ``/`` final.
    """
    header = b""
    header_file = dir_path / ".header"
    if header_file.is_file():
        try:
            header = header_file.read_bytes()
            if header and not header.endswith(b"\n"):
                header += b"\n"
        except OSError:
            header = b""

    base_sel = selector if selector.endswith("/") else selector + "/"
    dirs: list[str] = []
    files: list[str] = []
    try:
        for entry in sorted(dir_path.iterdir(), key=lambda p: p.name.lower()):
            name = entry.name
            if name.startswith(".") or name == "index":
                continue
            if entry.is_dir():
                dirs.append(f"=> {base_sel}{name}/ {name}/")
            elif entry.is_file():
                files.append(f"=> {base_sel}{name} {name}")
    except OSError:
        pass

    body_lines: list[str] = []
    if not header:
        body_lines.append(f"# runv.club — Nex: {selector}")
        body_lines.append("")
    body_lines.extend(dirs)
    body_lines.extend(files)
    if not dirs and not files:
        body_lines.append("(directório vazio)")
    if base_sel != "/":
        parent = base_sel.rstrip("/").rsplit("/", 1)[0] + "/"
        if not parent:
            parent = "/"
        body_lines.append("")
        body_lines.append(f"=> {parent} ..")
    body_lines.append("")
    return header + ("\n".join(body_lines)).encode("utf-8")


def not_found_response(selector: str) -> bytes:
    return (
        f"# 404 — não encontrado\n\n"
        f"O selector {selector!r} não existe neste servidor Nex.\n\n"
        f"=> / raiz\n"
    ).encode("utf-8")


def build_response(cfg: NexConfig, raw_selector: str, log: logging.Logger) -> bytes:
    """Constrói a resposta Nex completa para um selector cru do cliente."""
    try:
        selector = sanitize_selector(raw_selector)
    except ValueError:
        log.info("selector rejeitado (traversal): %r", raw_selector[:120])
        return not_found_response(raw_selector.strip()[:120])

    kind, path, username = resolve_selector_path(cfg, selector)

    if kind == "users_index":
        return render_members_index(cfg)

    if kind == "user" and path is None:
        return not_found_response(selector)

    if path is None:
        return not_found_response(selector)

    # Raiz sem index próprio: se /var/nex/index não existir, listar.
    if path.is_dir():
        index_file = path / "index"
        if index_file.is_file():
            try:
                return index_file.read_bytes()
            except OSError:
                return not_found_response(selector)
        return render_directory_listing(path, selector)

    if path.is_file():
        try:
            return path.read_bytes()
        except OSError:
            return not_found_response(selector)

    # Selector "/" sem /var/nex/index nem directório: índice sintético.
    if selector == "/":
        return render_root_fallback(cfg)

    return not_found_response(selector)


def render_root_fallback(cfg: NexConfig) -> bytes:
    lines = [
        f"# {cfg.hostname} — Nex",
        "",
        "Bem-vindo ao espaço Nex do runv.club, uma pubnix da small web.",
        "",
        "=> /users/ Cápsulas dos membros",
        "",
    ]
    return ("\n".join(lines)).encode("utf-8")


# ---------------------------------------------------------------------------
# Servidor TCP
# ---------------------------------------------------------------------------
class NexTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, server_address, handler_cls, cfg: NexConfig, log: logging.Logger):
        self.cfg = cfg
        self.log = log
        super().__init__(server_address, handler_cls)


class NexRequestHandler(socketserver.BaseRequestHandler):
    def handle(self) -> None:
        server: NexTCPServer = self.server  # type: ignore[assignment]
        cfg = server.cfg
        log = server.log
        try:
            self.request.settimeout(READ_TIMEOUT_S)
            raw = self._read_selector()
        except (OSError, socket.timeout):
            return
        peer = self.client_address[0] if self.client_address else "?"
        try:
            response = build_response(cfg, raw, log)
        except Exception as e:  # nunca derrubar o servidor por uma request
            log.warning("erro a servir %r de %s: %s", raw[:120], peer, e)
            response = not_found_response(raw.strip()[:120])
        log.info("%s -> %r (%d bytes)", peer, raw.strip()[:120], len(response))
        try:
            self.request.sendall(response)
        except OSError:
            pass

    def _read_selector(self) -> str:
        chunks: list[bytes] = []
        total = 0
        while total < MAX_SELECTOR_BYTES:
            data = self.request.recv(1024)
            if not data:
                break
            chunks.append(data)
            total += len(data)
            if b"\n" in data:
                break
        blob = b"".join(chunks)
        line = blob.split(b"\n", 1)[0]
        return line.decode("utf-8", errors="replace")


def setup_logging(verbose: bool) -> logging.Logger:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    return logging.getLogger("nexd")


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Servidor Nex (porta 1900) do runv.club.")
    p.add_argument("--root", type=Path, default=DEFAULT_ROOT, help=f"raiz do sistema (padrão {DEFAULT_ROOT})")
    p.add_argument("--homes-root", type=Path, default=DEFAULT_HOMES_ROOT, help="raiz das homes (padrão /home)")
    p.add_argument("--host", default=DEFAULT_HOST, help=f"endereço de escuta (padrão {DEFAULT_HOST})")
    p.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"porta TCP (padrão {DEFAULT_PORT})")
    p.add_argument("--hostname", default="runv.club", help="hostname público exibido no conteúdo")
    p.add_argument("--verbose", action="store_true", help="log detalhado")
    p.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    log = setup_logging(args.verbose)
    cfg = NexConfig(root=args.root, homes_root=args.homes_root, hostname=args.hostname)
    if not cfg.root.is_dir():
        log.warning("raiz %s inexistente — a servir mesmo assim (índice sintético em /)", cfg.root)
    server = NexTCPServer((args.host, args.port), NexRequestHandler, cfg, log)
    log.info("nexd %s à escuta em %s:%d (root=%s homes=%s)", VERSION, args.host, args.port, cfg.root, cfg.homes_root)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("a terminar (SIGINT)")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
