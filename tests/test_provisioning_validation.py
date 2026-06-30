"""
Comportamento das validações do provisionador (``create_runv_user.py``), o caminho
que corre como root. Confirma que entradas perigosas são rejeitadas e que as
válidas passam — incluindo a regressão dos nomes reservados ``entre``/``join``/
``welcome`` que faltavam neste módulo.

Só biblioteca padrão.
"""

from __future__ import annotations

import unittest

import _support

# Nome improvável de existir no sistema de teste (validate_username consulta o
# /etc/passwd via pwd.getpwnam para o caso "válido").
_FREE_NAME = "runvtest_zzqx9"


@unittest.skipUnless(_support.LOADED, _support.SKIP_REASON)
class ValidateUsername(unittest.TestCase):
    def setUp(self) -> None:
        self.cru = _support.create_runv_user

    def test_accepts_well_formed(self) -> None:
        self.assertEqual(self.cru.validate_username(_FREE_NAME), _FREE_NAME)

    def test_rejects_reserved_system_names(self) -> None:
        for name in ("root", "www-data", "admin"):
            with self.assertRaises(self.cru.ValidationError):
                self.cru.validate_username(name)

    def test_rejects_reserved_site_routes(self) -> None:
        # Estes faltavam em create_runv_user.py antes da correção da auditoria.
        for name in ("entre", "join", "welcome"):
            with self.assertRaises(self.cru.ValidationError):
                self.cru.validate_username(name)

    def test_rejects_bad_shapes(self) -> None:
        for bad in ("Alice", "1bob", "a", "bob ", " bob", "bad.name", "bad/name", ""):
            with self.assertRaises(self.cru.ValidationError):
                self.cru.validate_username(bad)


@unittest.skipUnless(_support.LOADED, _support.SKIP_REASON)
class ValidateEmail(unittest.TestCase):
    def setUp(self) -> None:
        self.cru = _support.create_runv_user

    def test_accepts_well_formed(self) -> None:
        self.assertEqual(self.cru.validate_email("ana@exemplo.org"), "ana@exemplo.org")

    def test_rejects_empty_and_malformed(self) -> None:
        for bad in ("", "sem-arroba", "a@@b.co", "ana@", "@exemplo.org"):
            with self.assertRaises(self.cru.ValidationError):
                self.cru.validate_email(bad)

    def test_rejects_overlong(self) -> None:
        too_long = ("a" * 250) + "@x.co"  # > 254 chars
        self.assertGreater(len(too_long), self.cru.MAX_EMAIL_LEN)
        with self.assertRaises(self.cru.ValidationError):
            self.cru.validate_email(too_long)

    def test_rejects_surrounding_space(self) -> None:
        with self.assertRaises(self.cru.ValidationError):
            self.cru.validate_email(" ana@exemplo.org")


@unittest.skipUnless(_support.LOADED, _support.SKIP_REASON)
class NormalizePublicKey(unittest.TestCase):
    def setUp(self) -> None:
        self.cru = _support.create_runv_user

    def test_normalizes_valid_key_with_comment(self) -> None:
        raw = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIabcDEF123+/xyz000 ana@maquina"
        out = self.cru.normalize_public_key(raw)
        self.assertTrue(out.startswith("ssh-ed25519 AAAAC3"))
        self.assertTrue(out.endswith("ana@maquina"))

    def test_rejects_unknown_type(self) -> None:
        with self.assertRaises(self.cru.ValidationError):
            self.cru.normalize_public_key("ssh-foo AAAAB3Nza+/abc==")

    def test_rejects_embedded_newline(self) -> None:
        with self.assertRaises(self.cru.ValidationError):
            self.cru.normalize_public_key("ssh-ed25519 AAAA\nBBBB")

    def test_rejects_non_base64_blob(self) -> None:
        with self.assertRaises(self.cru.ValidationError):
            self.cru.normalize_public_key("ssh-ed25519 not*valid*base64!")


if __name__ == "__main__":
    unittest.main()
