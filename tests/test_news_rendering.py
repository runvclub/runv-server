"""
Regressão de segurança para o gerador de notícias (``site/news/publish_news.py``).

O ``body_html`` é renderizado no cliente via ``innerHTML`` (news-page.js) — logo o
gerador TEM de produzir HTML seguro: escapar todo o conteúdo e nunca emitir
``javascript:`` em hrefs. Estes testes travam essa propriedade para que uma futura
alteração ao renderizador não reintroduza XSS armazenado, e confirmam que a
formatação legítima continua a funcionar.

Só biblioteca padrão.
"""

from __future__ import annotations

import unittest

import _support


@unittest.skipUnless(_support.LOADED, _support.SKIP_REASON)
class MarkdownEscaping(unittest.TestCase):
    def setUp(self) -> None:
        self.pn = _support.publish_news

    def test_script_tag_is_escaped_markdown(self) -> None:
        out = self.pn.render_markdown_html("<script>alert('xss')</script>")
        self.assertNotIn("<script>", out)
        self.assertIn("&lt;script&gt;", out)

    def test_script_tag_is_escaped_plaintext(self) -> None:
        out = self.pn.render_plain_text_html("oi <script>alert(1)</script> tchau")
        self.assertNotIn("<script>", out)
        self.assertIn("&lt;script&gt;", out)

    def test_img_onerror_payload_is_neutralized(self) -> None:
        out = self.pn.render_markdown_html('<img src=x onerror="alert(1)">')
        # A tag inteira fica escapada como texto inerte: não há elemento <img>
        # real, logo o onerror nunca dispara (o substring escapado é inofensivo).
        self.assertNotIn("<img", out)
        self.assertIn("&lt;img", out)

    def test_legit_formatting_still_renders(self) -> None:
        out = self.pn.render_markdown_html("isto é **importante**")
        self.assertIn("<strong>importante</strong>", out)


@unittest.skipUnless(_support.LOADED, _support.SKIP_REASON)
class SafeHref(unittest.TestCase):
    def setUp(self) -> None:
        self.pn = _support.publish_news

    def test_https_allowed(self) -> None:
        self.assertIsNotNone(self.pn._safe_href("https://runv.club/x"))

    def test_relative_and_mailto_allowed(self) -> None:
        self.assertIsNotNone(self.pn._safe_href("mailto:ana@runv.club"))
        self.assertIsNotNone(self.pn._safe_href("/wiki/"))

    def test_javascript_scheme_rejected(self) -> None:
        self.assertIsNone(self.pn._safe_href("javascript:alert(1)"))

    def test_data_scheme_rejected(self) -> None:
        self.assertIsNone(self.pn._safe_href("data:text/html,<script>"))

    def test_markdown_link_with_js_scheme_is_not_an_href(self) -> None:
        out = self.pn.inline_markdown_to_html("clique [aqui](javascript:alert(1))")
        self.assertNotIn('href="javascript', out)


if __name__ == "__main__":
    unittest.main()
