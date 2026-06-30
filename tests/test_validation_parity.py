"""
Trava a duplicação intencional das constantes de política de validação.

``terminal/entre_core.py`` (recolha na fila, input não-confiável) e os scripts de
administração ``create_runv_user.py`` / ``update_user.py`` / ``del-user.py``
mantêm cópias próprias de ``USERNAME_PATTERN``, ``EMAIL_PATTERN``,
``ALLOWED_KEY_TYPES``, ``RESERVED_USERNAMES`` e ``MAX_EMAIL_LEN`` por desenho — os
módulos são instalados em locais diferentes e não se importam em runtime.

O risco dessa duplicação é o *drift*: uma regra muda num lado e não no outro,
abrindo um buraco silencioso (ex.: um nome reservado no cadastro mas criável pelo
provisionador). Estes testes asseguram que as cópias permanecem idênticas.

Só biblioteca padrão; corre com ``python3 -m unittest discover -s tests``.
"""

from __future__ import annotations

import unittest

import _support


@unittest.skipUnless(_support.LOADED, _support.SKIP_REASON)
class ValidationParity(unittest.TestCase):
    def test_username_pattern_identical(self) -> None:
        ref = _support.entre_core.USERNAME_PATTERN.pattern
        for mod in (
            _support.create_runv_user,
            _support.update_user,
            _support.del_user,
            _support.build_directory,
        ):
            self.assertEqual(
                mod.USERNAME_PATTERN.pattern,
                ref,
                msg=f"USERNAME_PATTERN divergente em {mod.__name__}",
            )

    def test_email_pattern_identical(self) -> None:
        ref = _support.entre_core.EMAIL_PATTERN.pattern
        for mod in (_support.create_runv_user, _support.update_user):
            self.assertEqual(
                mod.EMAIL_PATTERN.pattern,
                ref,
                msg=f"EMAIL_PATTERN divergente em {mod.__name__}",
            )

    def test_allowed_key_types_identical(self) -> None:
        ref = tuple(_support.entre_core.ALLOWED_KEY_TYPES)
        for mod in (_support.create_runv_user, _support.update_user):
            self.assertEqual(
                tuple(mod.ALLOWED_KEY_TYPES),
                ref,
                msg=f"ALLOWED_KEY_TYPES divergente em {mod.__name__}",
            )

    def test_reserved_usernames_identical(self) -> None:
        ref = set(_support.entre_core.RESERVED_USERNAMES)
        for mod in (_support.create_runv_user, _support.del_user):
            got = set(mod.RESERVED_USERNAMES)
            self.assertEqual(
                got,
                ref,
                msg=(
                    f"RESERVED_USERNAMES divergente em {mod.__name__}; "
                    f"diferença simétrica: {sorted(got ^ ref)}"
                ),
            )

    def test_reserved_includes_site_routes(self) -> None:
        # Regressão: os nomes do próprio onboarding/site têm de estar reservados
        # em TODAS as cópias (foi exatamente o drift encontrado na auditoria).
        for mod in (
            _support.entre_core,
            _support.create_runv_user,
            _support.del_user,
        ):
            reserved = set(mod.RESERVED_USERNAMES)
            for name in ("entre", "join", "welcome"):
                self.assertIn(
                    name,
                    reserved,
                    msg=f"{name!r} deveria estar reservado em {mod.__name__}",
                )

    def test_max_email_len_identical(self) -> None:
        ref = _support.entre_core.MAX_EMAIL_LEN
        for mod in (_support.create_runv_user, _support.update_user):
            self.assertEqual(
                mod.MAX_EMAIL_LEN,
                ref,
                msg=f"MAX_EMAIL_LEN divergente em {mod.__name__}",
            )


if __name__ == "__main__":
    unittest.main()
