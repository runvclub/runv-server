"""
Trava a paridade do dicionário bilíngue do fluxo «entre» (terminal/i18n.py) e a
existência dos templates localizados em terminal/templates/en/.

Mesma filosofia de test_validation_parity.py: duplicação (aqui, entre os dois
idiomas) é aceitável por desenho, mas uma chave/arquivo faltando num dos lados
é um bug silencioso — o visitante veria uma mensagem na língua errada ou um
template ausente.

Só biblioteca padrão.
"""

from __future__ import annotations

import unittest
from pathlib import Path

import _support

VISITOR_FACING_TEMPLATES = (
    "intro.txt",
    "warning_public_key.txt",
    "confirm.txt",
    "goodbye.txt",
)

# Só o admin lê estes — não precisam de versão em inglês.
ADMIN_ONLY_TEMPLATES = (
    "admin_console_notice.txt",
    "admin_mail.txt",
)


@unittest.skipUnless(_support.LOADED, _support.SKIP_REASON)
class I18nStringParity(unittest.TestCase):
    def test_same_keys_in_both_languages(self) -> None:
        i18n = _support.i18n
        pt_keys = set(i18n.STRINGS["pt"])
        en_keys = set(i18n.STRINGS["en"])
        self.assertEqual(
            pt_keys,
            en_keys,
            msg=f"chaves divergentes entre pt/en: {sorted(pt_keys ^ en_keys)}",
        )

    def test_no_empty_strings(self) -> None:
        i18n = _support.i18n
        for lang, table in i18n.STRINGS.items():
            for key, value in table.items():
                self.assertTrue(value.strip(), msg=f"{lang}.{key} está vazio")

    def test_t_looks_up_and_formats(self) -> None:
        i18n = _support.i18n
        self.assertEqual(i18n.t("pt", "confirm_prompt_label"), "Opção: ")
        self.assertEqual(i18n.t("en", "confirm_prompt_label"), "Option: ")
        formatted = i18n.t("en", "err_online_presence_required", min_len=16)
        self.assertIn("16", formatted)

    def test_t_falls_back_to_default_lang_for_unknown_lang(self) -> None:
        i18n = _support.i18n
        self.assertEqual(
            i18n.t("fr", "confirm_prompt_label"),
            i18n.t(i18n.DEFAULT_LANG, "confirm_prompt_label"),
        )


@unittest.skipUnless(_support.LOADED, _support.SKIP_REASON)
class VisitorTemplatesExistInBothLocales(unittest.TestCase):
    def setUp(self) -> None:
        self.pt_dir = _support.REPO_ROOT / "terminal" / "templates"
        self.en_dir = self.pt_dir / "en"

    def test_pt_template_exists(self) -> None:
        for name in VISITOR_FACING_TEMPLATES:
            self.assertTrue((self.pt_dir / name).is_file(), msg=f"faltando: {name} (pt)")

    def test_en_template_exists(self) -> None:
        for name in VISITOR_FACING_TEMPLATES:
            self.assertTrue((self.en_dir / name).is_file(), msg=f"faltando: {name} (en)")

    def test_admin_only_templates_stay_pt_only(self) -> None:
        # Não é obrigatório NÃO existir uma versão en/ um dia, mas hoje o fluxo
        # não a usa — confirma que o par pt existe e que não criamos uma en/
        # órfã sem ligar a `template_for` (o que indicaria código morto).
        for name in ADMIN_ONLY_TEMPLATES:
            self.assertTrue((self.pt_dir / name).is_file(), msg=f"faltando: {name} (pt)")
            self.assertFalse(
                (self.en_dir / name).is_file(),
                msg=f"{name} tem versão en/ não utilizada por template_for()",
            )


@unittest.skipUnless(_support.LOADED, _support.SKIP_REASON)
class EntreCoreValidatorsRespectLang(unittest.TestCase):
    """entre_core.py é o caminho de input não-confiável (visitante via SSH);
    confirma que a mensagem de erro sai no idioma pedido, não só em pt fixo."""

    def setUp(self) -> None:
        self.ec = _support.entre_core

    def test_username_error_pt_vs_en(self) -> None:
        with self.assertRaises(self.ec.ValidationError) as pt_ctx:
            self.ec.validate_username("root", lang="pt")
        with self.assertRaises(self.ec.ValidationError) as en_ctx:
            self.ec.validate_username("root", lang="en")
        self.assertIn("reservado", str(pt_ctx.exception))
        self.assertIn("reserved", str(en_ctx.exception))

    def test_email_error_pt_vs_en(self) -> None:
        with self.assertRaises(self.ec.ValidationError) as pt_ctx:
            self.ec.validate_email("sem-arroba", lang="pt")
        with self.assertRaises(self.ec.ValidationError) as en_ctx:
            self.ec.validate_email("sem-arroba", lang="en")
        self.assertIn("endereço", str(pt_ctx.exception))
        self.assertIn("address", str(en_ctx.exception))

    def test_pubkey_error_pt_vs_en(self) -> None:
        with self.assertRaises(self.ec.ValidationError) as pt_ctx:
            self.ec.normalize_public_key("ssh-foo AAAAB3==", lang="pt")
        with self.assertRaises(self.ec.ValidationError) as en_ctx:
            self.ec.normalize_public_key("ssh-foo AAAAB3==", lang="en")
        self.assertIn("não aceite", str(pt_ctx.exception))
        self.assertIn("not accepted", str(en_ctx.exception))

    def test_default_lang_unchanged_for_existing_callers(self) -> None:
        # create_runv_user.py chama as SUAS PRÓPRIAS cópias (não estas) — mas
        # qualquer chamador futuro sem `lang` explícito deve continuar em pt,
        # preservando o comportamento anterior a esta mudança.
        with self.assertRaises(self.ec.ValidationError) as ctx:
            self.ec.validate_username("root")
        self.assertIn("reservado", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
