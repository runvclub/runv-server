"""
Derivação do endereço ``.b32.i2p`` a partir do ficheiro de chaves do i2pd
(``setup_i2p.destination_b32`` / ``_destination_length``).

O endereço é ``base32(sha256(Destination))`` em minúsculas e sem padding, onde a
Destination (KeysAndCert) tem 256+128 bytes de chaves + um certificado
(tipo[1] + tamanho[2] + payload). Estes testes constroem Destinations sintéticas
e confirmam o comprimento parseado e a codificação — sem precisar de i2pd nem root.

setup_i2p importa setup_alt_protocols (grp/pwd), por isso corre só em Unix.

Só biblioteca padrão.
"""

from __future__ import annotations

import base64
import hashlib
import tempfile
import unittest
from pathlib import Path

import _support

setup_i2p = _support.setup_i2p


def _expected_b32(dest: bytes) -> str:
    digest = hashlib.sha256(dest).digest()
    return base64.b32encode(digest).decode("ascii").lower().rstrip("=") + ".b32.i2p"


@unittest.skipUnless(setup_i2p is not None, "módulo setup_i2p não pôde ser carregado")
class DestinationLength(unittest.TestCase):
    def test_null_certificate_is_387(self) -> None:
        # cert tipo 0, tamanho 0 → Destination = 384 + 3 = 387 bytes.
        data = b"\x11" * 384 + b"\x00" + b"\x00\x00" + b"trailing-private-keys"
        self.assertEqual(setup_i2p._destination_length(data), 387)

    def test_key_certificate_is_391(self) -> None:
        # cert tipo 5 (key cert), tamanho 4 → Destination = 384 + 3 + 4 = 391 bytes.
        data = b"\x22" * 384 + b"\x05" + b"\x00\x04" + b"\x00\x07\x00\x00" + b"privkeys"
        self.assertEqual(setup_i2p._destination_length(data), 391)

    def test_too_short_returns_none(self) -> None:
        self.assertIsNone(setup_i2p._destination_length(b"\x00" * 100))

    def test_truncated_payload_returns_none(self) -> None:
        # Anuncia payload de 4 bytes mas não os inclui.
        data = b"\x00" * 384 + b"\x05" + b"\x00\x04"
        self.assertIsNone(setup_i2p._destination_length(data))


@unittest.skipUnless(setup_i2p is not None, "módulo setup_i2p não pôde ser carregado")
class DestinationB32(unittest.TestCase):
    def test_encoding_is_lower_unpadded_52_chars(self) -> None:
        dest = bytes(range(256)) + b"\x33" * 128 + b"\x00\x00\x00"  # null cert, 387 bytes
        with tempfile.TemporaryDirectory() as d:
            dat = Path(d) / "runv-i2p-x.dat"
            dat.write_bytes(dest + b"\xAA" * 640)  # + chaves privadas a seguir
            got = setup_i2p.destination_b32(dat)
        self.assertIsNotNone(got)
        assert got is not None
        self.assertTrue(got.endswith(".b32.i2p"))
        label = got[: -len(".b32.i2p")]
        self.assertEqual(len(label), 52, "hash de 32 bytes → 52 chars base32 sem padding")
        self.assertEqual(label, label.lower())
        self.assertNotIn("=", label)

    def test_hashes_only_destination_not_private_keys(self) -> None:
        dest = b"\x44" * 384 + b"\x00\x00\x00"  # null cert
        with tempfile.TemporaryDirectory() as d:
            dat = Path(d) / "runv-i2p-y.dat"
            dat.write_bytes(dest + b"\x99" * 300)
            got = setup_i2p.destination_b32(dat)
        self.assertEqual(got, _expected_b32(dest))

    def test_missing_file_returns_none(self) -> None:
        self.assertIsNone(setup_i2p.destination_b32(Path("/nonexistent/runv-i2p-z.dat")))


if __name__ == "__main__":
    unittest.main()
