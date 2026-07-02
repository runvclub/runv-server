"""
Segurança e correção do saneamento de selector do nexd (servidor Nex).

O nexd serve conteúdo cru a partir de ``/var/nex`` e de ``/home/<user>/public_nex``;
um selector malicioso não pode escapar dessas raízes. Estes testes cobrem as
funções puras (``sanitize_selector``, ``resolve_selector_path``, ``_safe_join``) —
não precisam de root nem de sockets, e correm em qualquer plataforma porque o nexd
tolera a ausência de ``pwd``.

Só biblioteca padrão.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import _support

nexd = _support.nexd


@unittest.skipUnless(nexd is not None, "módulo nexd não pôde ser carregado")
class SanitizeSelector(unittest.TestCase):
    def test_empty_becomes_root(self) -> None:
        self.assertEqual(nexd.sanitize_selector(""), "/")
        self.assertEqual(nexd.sanitize_selector("  \r\n"), "/")

    def test_prepends_leading_slash(self) -> None:
        self.assertEqual(nexd.sanitize_selector("users/maria"), "/users/maria")

    def test_preserves_trailing_slash(self) -> None:
        self.assertEqual(nexd.sanitize_selector("/users/"), "/users/")

    def test_collapses_dot_and_empty_components(self) -> None:
        self.assertEqual(nexd.sanitize_selector("/a//./b"), "/a/b")

    def test_strips_crlf(self) -> None:
        self.assertEqual(nexd.sanitize_selector("/a/b\r\n"), "/a/b")

    def test_rejects_parent_traversal(self) -> None:
        for bad in ("/../etc/passwd", "/users/../../root", "/a/b/../../../x"):
            with self.assertRaises(ValueError):
                nexd.sanitize_selector(bad)


@unittest.skipUnless(nexd is not None, "módulo nexd não pôde ser carregado")
class SafeJoin(unittest.TestCase):
    def test_stays_within_base(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            (base / "sub").mkdir()
            got = nexd._safe_join(base, ["sub"])
            self.assertIsNotNone(got)
            self.assertEqual(got, (base / "sub").resolve())

    def test_symlink_escape_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td) / "base"
            base.mkdir()
            outside = Path(td) / "secret"
            outside.mkdir()
            link = base / "escape"
            try:
                link.symlink_to(outside)
            except (OSError, NotImplementedError):
                self.skipTest("symlinks indisponíveis nesta plataforma")
            # Resolver através do symlink cai fora de base → deve ser bloqueado.
            self.assertIsNone(nexd._safe_join(base, ["escape", "x"]))


@unittest.skipUnless(nexd is not None, "módulo nexd não pôde ser carregado")
class ResolveSelectorPath(unittest.TestCase):
    def _cfg(self, root: Path, homes: Path):
        return nexd.NexConfig(root=root, homes_root=homes, hostname="runv.club")

    def test_users_index(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            cfg = self._cfg(Path(td) / "nex", Path(td) / "home")
            kind, path, user = nexd.resolve_selector_path(cfg, "/users/")
            self.assertEqual(kind, "users_index")
            self.assertIsNone(path)

    def test_user_maps_to_public_nex(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            homes = Path(td) / "home"
            (homes / "maria" / "public_nex").mkdir(parents=True)
            cfg = self._cfg(Path(td) / "nex", homes)
            kind, path, user = nexd.resolve_selector_path(cfg, "/users/maria/")
            self.assertEqual(kind, "user")
            self.assertEqual(user, "maria")
            self.assertEqual(path, (homes / "maria" / "public_nex").resolve())

    def test_invalid_username_yields_none_path(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            cfg = self._cfg(Path(td) / "nex", Path(td) / "home")
            kind, path, user = nexd.resolve_selector_path(cfg, "/users/root/")
            self.assertEqual(kind, "user")
            self.assertIsNone(path)  # 'root' está em SKIP_USERS

    def test_root_path_under_nex_root(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "nex"
            root.mkdir()
            cfg = self._cfg(root, Path(td) / "home")
            kind, path, user = nexd.resolve_selector_path(cfg, "/pagina")
            self.assertEqual(kind, "root")
            self.assertEqual(path, (root / "pagina").resolve())


if __name__ == "__main__":
    unittest.main()
