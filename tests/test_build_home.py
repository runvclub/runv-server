"""
Garantias da home gerada (``site/build_home.py``).

  1. A home só publica o que já é público: username e datas. Campos privados
     que por engano apareçam no members.json (email, fingerprint, quota) nunca
     chegam ao HTML.
  2. Usernames fora da política são descartados e nada do members.json é
     inserido sem escape.
  3. Linhas mal formadas no diário são ignoradas sem derrubar a geração.
  4. Gera pt e en, cada uma com o hreflang da outra.

Não depende de Unix (build_home não lê users.json nem precisa de root), por isso
corre também em Windows. Só biblioteca padrão.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "site" / "build_home.py"

_SECRET_EMAIL = "alice@secret.example"
_SECRET_FP = "SHA256:deadbeefdeadbeefdeadbeef"

_MEMBERS = [
    {
        "username": "alice",
        "since": "2026-01-02T00:00:00+00:00",
        "path": "/~alice/",
        "homepage_mtime": "2026-03-01T12:00:00+00:00",
        "email": _SECRET_EMAIL,
        "public_key_fingerprint": _SECRET_FP,
        "quota_soft_mb": 450,
    },
    {"username": "bob", "since": "2026-02-01T10:00:00+00:00", "path": "/~bob/",
     "homepage_mtime": "2026-02-01T10:00:05+00:00"},
    {"username": "<script>alert(1)</script>", "since": "2026-01-04", "path": "/~x/"},
    {"username": "Bad Name", "since": "2026-01-05", "path": "/~y/"},
]

_DIARY = """# comentário
2026-09-01 | Entrada boa | Good entry
isto não é uma entrada
2026-13-40 | data inválida | bad date
2026-09-02 | <b>sem html</b> | <b>no html</b>
"""


class BuildHome(unittest.TestCase):
    def _build(self, members: list) -> tuple[str, str, str]:
        with tempfile.TemporaryDirectory() as td:
            t = Path(td)
            (t / "members.json").write_text(json.dumps(members), encoding="utf-8")
            (t / "diario.txt").write_text(_DIARY, encoding="utf-8")
            (t / "home.pt.txt").write_text("Texto pt.\n", encoding="utf-8")
            (t / "home.en.txt").write_text("Text en.\n", encoding="utf-8")
            (t / "facts.json").write_text(json.dumps({"os": "Debian 13", "cpus": 6, "mem_gb": 12, "disk_gb": 394}), encoding="utf-8")
            proc = subprocess.run(
                [
                    sys.executable, str(SCRIPT),
                    "--out-dir", str(t / "out"),
                    "--members-json", str(t / "members.json"),
                    "--diary", str(t / "diario.txt"),
                    "--manifesto-dir", str(t),
                    "--facts-json", str(t / "facts.json"),
                    "--now", "2026-09-24T12:00:00Z",
                ],
                capture_output=True, text=True, encoding="utf-8",
                env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            pt = (t / "out" / "index.html").read_text(encoding="utf-8")
            en = (t / "out" / "en" / "index.html").read_text(encoding="utf-8")
            return pt, en, proc.stderr

    def test_private_fields_never_published(self) -> None:
        pt, en, _ = self._build(_MEMBERS)
        for page in (pt, en):
            self.assertNotIn(_SECRET_EMAIL, page)
            self.assertNotIn(_SECRET_FP, page)
            self.assertNotIn("quota", page)

    def test_invalid_usernames_dropped_and_escaped(self) -> None:
        pt, _, _ = self._build(_MEMBERS)
        self.assertIn('href="/~alice/"', pt)
        self.assertIn('href="/~bob/"', pt)
        self.assertNotIn("<script>alert", pt)
        self.assertNotIn("Bad Name", pt)
        self.assertIn("2 contas ativas", pt)

    def test_sorted_by_update_and_placeholder_detected(self) -> None:
        pt, _, _ = self._build(_MEMBERS)
        self.assertLess(pt.index("~alice"), pt.index("~bob"))
        # bob mexeu no index.html segundos depois de criar a conta: ainda é o placeholder.
        self.assertIn("página padrão", pt)

    def test_bad_diary_lines_skipped(self) -> None:
        pt, en, err = self._build(_MEMBERS)
        self.assertIn("Entrada boa", pt)
        self.assertIn("Good entry", en)
        self.assertIn("&lt;b&gt;sem html&lt;/b&gt;", pt)
        self.assertNotIn("<b>sem html</b>", pt)
        self.assertIn("ignorada", err)

    def test_both_locales_with_hreflang(self) -> None:
        pt, en, _ = self._build(_MEMBERS)
        self.assertIn('<html lang="pt-BR">', pt)
        self.assertIn('<html lang="en">', en)
        for page in (pt, en):
            self.assertIn('hreflang="en" href="https://runv.club/en/"', page)
            self.assertIn('hreflang="pt-BR" href="https://runv.club/"', page)

    def test_empty_members(self) -> None:
        pt, en, _ = self._build([])
        self.assertIn("nenhuma conta", pt)
        self.assertIn("no accounts", en)


if __name__ == "__main__":
    unittest.main()
