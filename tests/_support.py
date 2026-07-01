"""
Suporte comum aos testes do runv-server.

Os módulos de provisionamento exigem Unix (importam ``pwd``/``fcntl`` e usam
``os.geteuid``), por isso os testes são automaticamente ignorados em plataformas
sem esses módulos (ex.: Windows nativo). Em Linux/WSL correm normalmente.

Carrega os módulos relevantes a partir das suas pastas de instalação (que não se
importam umas às outras em runtime) para que os testes de paridade possam comparar
as constantes de política lado a lado.

Só biblioteca padrão.
"""

from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Pastas que contêm os módulos sob teste (espelha a topologia de instalação).
_SOURCE_DIRS = [
    REPO_ROOT / "terminal",
    REPO_ROOT / "scripts" / "admin",
    REPO_ROOT / "site",
    REPO_ROOT / "site" / "news",
    REPO_ROOT / "email",
    Path(__file__).resolve().parent,  # a própria pasta tests/ (para `import _support`)
]
for _d in _SOURCE_DIRS:
    _s = str(_d)
    if _s not in sys.path:
        sys.path.insert(0, _s)


def _load_from_path(module_name: str, rel_path: str):
    """Carrega um módulo cujo ficheiro tem um nome não-importável (ex.: del-user.py)."""
    path = REPO_ROOT / rel_path
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:  # pragma: no cover
        raise ImportError(f"não foi possível carregar {rel_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


LOADED = False
SKIP_REASON = ""

entre_core = None
create_runv_user = None
update_user = None
del_user = None
build_directory = None
publish_news = None
i18n = None

try:
    entre_core = importlib.import_module("entre_core")
    create_runv_user = importlib.import_module("create_runv_user")
    update_user = importlib.import_module("update_user")
    build_directory = importlib.import_module("build_directory")
    publish_news = importlib.import_module("publish_news")
    del_user = _load_from_path("del_user", "scripts/admin/del-user.py")
    i18n = importlib.import_module("i18n")
    LOADED = True
except Exception as exc:  # pragma: no cover - depende de SO Unix
    SKIP_REASON = (
        "módulos do runv exigem ambiente Unix (pwd/fcntl/geteuid): "
        f"{type(exc).__name__}: {exc}"
    )
