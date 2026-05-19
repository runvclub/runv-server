# Revisão: aliases de email (Parte 2)

[← Índice](README.md)

Registo da revisão de código e validação. Atualizar a secção **VPS** após correr o smoke test no servidor.

| Campo | Valor |
|-------|--------|
| Data | 2026-05-19 |
| Commit | `e357e93` (ajustar após `git rev-parse HEAD` no deploy) |
| Revisor | Automatizado + checklist manual |

## Fase 1 — Estática (Windows / clone)

| Item | Resultado | Notas |
|------|-----------|--------|
| 1.1 Sem Mailgun/Postfix/DNS no código `tools/` | **PASS** | Grep sem matches |
| 1.1 Alias fixo `username@domínio` | **PASS** | `alias_address()` |
| 1.1 Usernames reservados | **PASS** | `ALIAS_RESERVED_USERNAMES` completo |
| 1.1 Validação destino | **PASS** | Script Python com 6 casos |
| 1.1 `O_EXCL` em pedidos | **PASS** | `create_pending_request()` |
| 1.1 Arquivo sem apagar | **PASS** | `archive_request()` |
| 1.1 Admin root | **PASS** | `require_root()` após `parse_args` |
| 1.1 Lock + escrita atómica | **PASS** | `approve_pending()` |
| 1.1 Setup idempotente | **PASS** | `setup_email_aliases.py` |
| 1.2 Sem leitura `users.json` nos bins membro | **PASS** | Só setup `--add-existing-users` |
| 1.3 `compileall` | **PASS** | |
| 1.3 `--help` (3 entrypoints) | **PASS** | |
| 1.3 `setup --dry-run` | **PASS** | |

### Correcções aplicadas na revisão

- Re-validação de `destination` em `approve_pending()` antes de gravar alias activo.
- Rejeição de `--reason` vazio em `runv-admin-email-alias reject`.
- Script [`scripts/admin/smoke_test_email_aliases.py`](../scripts/admin/smoke_test_email_aliases.py) para VPS/WSL.
- Secção em [14-smoke-tests-and-validation.md](14-smoke-tests-and-validation.md).

## Fase 2 — VPS Linux

### 2.3–2.5 Lógica (WSL, modo direct, temp dir)

| Secção | Resultado | Notas |
|--------|-----------|--------|
| 2.3 E2E request → approve → list | **PASS** | `smoke_test_email_aliases.py --user pablo` em WSL |
| 2.4 Validações / cancel / reject | **PASS** | mesmo script |
| 2.5 Alteração destino | **PASS** | `created_at` preservado |

### 2.2 / bins instalados (executar na VPS)

```bash
cd /caminho/para/runv-server
git pull
COMMIT=$(git rev-parse --short HEAD)
echo "Testando commit $COMMIT"

sudo python3 scripts/admin/setup_email_aliases.py --verbose
sudo python3 scripts/admin/setup_email_aliases.py --add-existing-users
cd tools && sudo python3 tools.py --verbose

sudo python3 scripts/admin/smoke_test_email_aliases.py --user SEU_MEMBRO_TESTE
```

| Secção | Resultado | Data / notas |
|--------|-----------|----------------|
| 2.2 Setup + instalação | _pendente VPS_ | `which`, `ls -la /var/lib/runv/email-*` |
| 2.2 Smoke subprocess (bins reais) | _pendente VPS_ | sem `--direct`; exige `sudo` |
| 2.6 Regressão Parte 1 | _pendente VPS_ | `runv-profile`, `runv-who`, etc. |
| 2.7 Docs vs saída real | **PASS** | revisão estática 08 + 17 |

### Permissões esperadas (2.2)

```text
/var/lib/runv/email-aliases.json      640 root:runv-members
/var/lib/runv/email-aliases.lock      660 root:runv-members
/var/lib/runv/email-alias-queue/      2770 root:runv-members
```

## Critérios finais

- [x] Fase 1 sem bloqueantes
- [x] Fase 2.3–2.5 lógica validada (WSL + smoke script)
- [ ] Fase 2.2 + smoke **subprocess** na VPS Debian (operador)
- [x] Nenhum código envia email ou configura Mailgun/DNS para aliases
- [x] Documentação 08 + 17 alinhada com implementação
- [ ] Operador confirmou passo manual pós-`approve` no provedor real

## Comando único recomendado na VPS

```bash
sudo python3 scripts/admin/smoke_test_email_aliases.py --user MEMBRO
```

Saída esperada final: `Smoke test aliases de email: PASS`
