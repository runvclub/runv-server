"""
Trava a lista de arquivos que ``setup_entre.py`` copia para o install-root
(``/opt/runv/terminal`` em produção).

Contexto: ``terminal/i18n.py`` foi adicionado numa sessão e ficou fora da lista
hardcoded de ``copy_module()`` — o módulo instalado em produção não tinha
``i18n.py``, e ``entre_app.py`` quebrou com ``ImportError`` na primeira conexão
de um visitante real, exigindo correção manual às pressas no servidor. Este
teste torna esse esquecimento estruturalmente impossível: qualquer novo
``.py`` de runtime em ``terminal/`` (que não seja o próprio instalador) tem
de aparecer em ``setup_entre.COPY_FILES``, senão a suíte falha antes de
qualquer deploy.

Só biblioteca padrão.
"""

from __future__ import annotations

import unittest

import _support

# O instalador não se copia a si mesmo; roda a partir do checkout.
NOT_RUNTIME_DEPS = {"setup_entre.py"}


@unittest.skipUnless(_support.LOADED, _support.SKIP_REASON)
class SetupEntreCopyList(unittest.TestCase):
    def test_every_top_level_py_file_is_copied(self) -> None:
        terminal_dir = _support.REPO_ROOT / "terminal"
        actual = {p.name for p in terminal_dir.glob("*.py")} - NOT_RUNTIME_DEPS
        listed = set(_support.setup_entre.COPY_FILES)
        missing = actual - listed
        self.assertFalse(
            missing,
            msg=(
                f"arquivo(s) .py em terminal/ ausentes de setup_entre.COPY_FILES: "
                f"{sorted(missing)} — adicione-os lá, senão a instalação em produção "
                f"fica incompleta e entre_app.py quebra por ImportError."
            ),
        )

    def test_copy_files_point_to_real_files(self) -> None:
        # O inverso também importa: uma entrada em COPY_FILES apontando para um
        # arquivo que não existe mais (renomeado/removido) falha silenciosamente
        # dentro de copy_module() (só copia se src.is_file()) — sem este teste,
        # ninguém notaria.
        terminal_dir = _support.REPO_ROOT / "terminal"
        for name in _support.setup_entre.COPY_FILES:
            self.assertTrue(
                (terminal_dir / name).is_file(),
                msg=f"COPY_FILES referencia {name!r}, que não existe em terminal/",
            )

    def test_copy_subdirs_point_to_real_dirs(self) -> None:
        terminal_dir = _support.REPO_ROOT / "terminal"
        for name in _support.setup_entre.COPY_SUBDIRS:
            self.assertTrue(
                (terminal_dir / name).is_dir(),
                msg=f"COPY_SUBDIRS referencia {name!r}, que não existe em terminal/",
            )


if __name__ == "__main__":
    unittest.main()
