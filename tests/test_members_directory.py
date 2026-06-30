"""
Garantias do diretório público de membros (``site/build_directory.py``).

Dois invariantes críticos:
  1. Só campos seguros (username, since, path) são publicados — nunca email,
     fingerprint de chave ou quota.
  2. Usernames que não correspondam à política são descartados, mesmo que
     ``users.json`` tenha sido editado à mão (defesa em profundidade).

Exercita o CLI real em ``--dry-run`` (escreve para stdout, não toca em ficheiros).

Só biblioteca padrão.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import _support

_SECRET_EMAIL = "alice@secret.example"
_SECRET_FP = "SHA256:deadbeefdeadbeefdeadbeef"

_USERS_FIXTURE = [
    {
        "username": "alice",
        "created_at": "2026-01-02T00:00:00+00:00",
        "email": _SECRET_EMAIL,
        "public_key": "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5secret",
        "public_key_fingerprint": _SECRET_FP,
        "quota_soft_mib": 450,
    },
    {"username": "Bad Name", "created_at": "2026-01-03", "email": "x@y.co"},
    {"username": "<script>alert(1)</script>", "created_at": "2026-01-04", "email": "z@y.co"},
]


@unittest.skipUnless(_support.LOADED, _support.SKIP_REASON)
class BuildDirectory(unittest.TestCase):
    def _run(self, users: list) -> list:
        script = _support.REPO_ROOT / "site" / "build_directory.py"
        env = dict(os.environ)
        # Autoriza o guard administrativo de forma determinística.
        env["SUDO_USER"] = ""
        env["USER"] = "runvtester"
        env["RUNV_ADMIN_USERS"] = "runvtester"
        with tempfile.TemporaryDirectory() as td:
            users_json = Path(td) / "users.json"
            users_json.write_text(json.dumps(users), encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, str(script), "--dry-run", "--users-json", str(users_json)],
                capture_output=True,
                text=True,
                env=env,
                timeout=60,
            )
        self.assertEqual(proc.returncode, 0, msg=f"stderr: {proc.stderr}")
        self.stdout = proc.stdout
        return json.loads(proc.stdout)

    def test_only_safe_fields_published(self) -> None:
        members = self._run(_USERS_FIXTURE)
        self.assertEqual(len(members), 1)
        entry = members[0]
        self.assertEqual(set(entry.keys()), {"username", "since", "path"})
        self.assertEqual(entry["username"], "alice")
        self.assertEqual(entry["path"], "/~alice/")
        self.assertEqual(entry["since"], "2026-01-02T00:00:00+00:00")

    def test_no_sensitive_data_leaks(self) -> None:
        self._run(_USERS_FIXTURE)
        self.assertNotIn(_SECRET_EMAIL, self.stdout)
        self.assertNotIn(_SECRET_FP, self.stdout)
        self.assertNotIn("public_key", self.stdout)
        self.assertNotIn("quota", self.stdout)

    def test_invalid_usernames_dropped(self) -> None:
        members = self._run(_USERS_FIXTURE)
        names = {m["username"] for m in members}
        self.assertNotIn("Bad Name", names)
        self.assertNotIn("<script>alert(1)</script>", names)


if __name__ == "__main__":
    unittest.main()
