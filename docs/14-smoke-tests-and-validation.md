# Smoke tests e validação

[← Índice](README.md)

## Sintaxe Python (todo o produto)

```bash
cd REPO
python3 -m compileall -q scripts terminal site tools email patches
```

**Esperado:** código de saída `0`.

## Submódulo email

```bash
cd REPO/email
python3 -m pytest tests/ -q
```

**Esperado:** testes passam (há `test_mailgun_client.py`).

## `build_directory.py`

```bash
python3 site/build_directory.py --users-json site/example-users.json --dry-run
```

**Esperado:** JSON no stdout com `username`, `since`, `path`.

## `--help` (requer Unix)

Vários scripts importam `fcntl` ou `grp` — **não executáveis** em Windows típico:

- `scripts/admin/create_runv_user.py --help`
- `terminal/setup_entre.py --help`
- `site/genlanding.py --help`

Em **Debian:** correr os `--help` acima e guardar a saída para operadores. Confirmar que `site/genlanding.py --help` lista **`--sync-public-only`**.

## Aliases de email para membros (Linux)

Revisão estática (qualquer OS):

```bash
python3 -m compileall -q tools scripts/admin/setup_email_aliases.py scripts/admin/smoke_test_email_aliases.py
python3 tools/bin/runv-email-alias --help
python3 tools/bin/runv-admin-email-alias --help
```

Smoke test integrado (VPS ou WSL; usa diretório temporário por defeito):

```bash
cd REPO
sudo python3 scripts/admin/smoke_test_email_aliases.py --user MEMBRO_TESTE
```

Setup + instalação em produção (antes do smoke com paths reais):

```bash
sudo python3 scripts/admin/setup_email_aliases.py --verbose
sudo python3 scripts/admin/setup_email_aliases.py --add-existing-users
cd tools && sudo python3 tools.py --verbose
```

Ver também [08-email.md](08-email.md) e [17-community-commands.md](17-community-commands.md). Registo de revisão: [review-email-aliases-signoff.md](review-email-aliases-signoff.md).

## O que **não** existe no repo (facto)

- **Sem** workflows `.github/workflows` na raiz do projecto runv (verificado por ausência de `.github/` no clone típico).
- **Sem** suite de testes para `entre_core` ou `build_directory` além do que está em `email/tests/`.

Próximo: [15-glossary-and-reference.md](15-glossary-and-reference.md).
