# Email (saída)

[← Índice](README.md)

## Arquitectura actual

- **Predefinição:** envio via **Mailgun HTTP API** (`email/configure_mailgun.py`).
- **Estado:** `/etc/runv-email.json`
- **Segredos:** `/etc/runv-email.secrets.json` (permissões restritas; não versionar).

## Modo legado

- SMTP via `msmtp` / `sendmail`: flags `--legacy-smtp` ou `configure_msmtp_legacy.py` (detalhes nas docstrings e `--help` dos scripts em `email/`).

## Biblioteca

- `email/lib/mailer.py` — envio reutilizável; templates em `email/templates/`.
- Variável `RUNV_EMAIL_ROOT` ou `email_package_root` no JSON para o fluxo `entre` localizar templates.

## Integração com `entre`

- Notificações ao admin usam `admin_email` no `config.toml` do terminal **ou** fallback em `/etc/runv-email.json` (comportamento verificado no código de `terminal/` + `email/lib`).

## O que o repo não é

- **Não** é MTA completo (não recebe correio para caixas locais de membros como produto deste repositório).

## Aliases de email para membros

O email transacional da runv.club (Mailgun, `/etc/runv-email.json`) continua separado deste fluxo.

Nesta etapa **não** há mailbox local nem caixa `@runv.club` no servidor. Um membro pode pedir um alias fixo:

`username@runv.club` → email externo de destino

O alias **não** é activado automaticamente: o membro pede no terminal, um admin aprova, e o registo fica em JSON local. Criar o encaminhamento real no provedor de email (Mailgun, DNS, etc.) continua a ser passo manual ou integração futura.

### Membro

```bash
runv-email-alias request usuario@example.org
runv-email-alias status
runv-email-alias cancel
```

O alias é sempre `username@runv.club` (username Unix do utilizador que corre o comando). Não é possível escolher outro nome de alias.

### Admin

```bash
sudo runv-admin-email-alias pending
sudo runv-admin-email-alias list
sudo runv-admin-email-alias approve pablo
sudo runv-admin-email-alias reject pablo --reason "email destino inválido"
```

### Setup inicial no servidor

```bash
sudo python3 scripts/admin/setup_email_aliases.py
sudo python3 scripts/admin/setup_email_aliases.py --add-existing-users
```

Depois instalar os comandos com `sudo python3 tools/tools.py` (ver [05-tools-and-system-experience.md](05-tools-and-system-experience.md)).

### Ficheiros e permissões

| Caminho | Função |
|---------|--------|
| `/var/lib/runv/email-aliases.json` | Aliases aprovados (activos) |
| `/var/lib/runv/email-aliases.lock` | Lock para escrita segura |
| `/var/lib/runv/email-alias-queue/` | Pedidos pendentes |
| `.../approved/`, `.../rejected/`, `.../cancelled/` | Histórico de pedidos |

Permissões sugeridas após o setup:

| Caminho | Modo | Dono:grupo |
|---------|------|------------|
| `/var/lib/runv/email-aliases.json` | 640 | root:runv-members |
| `/var/lib/runv/email-aliases.lock` | 660 | root:runv-members |
| `/var/lib/runv/email-alias-queue/` | 2770 | root:runv-members |

Variáveis de ambiente para testes locais: `RUNV_EMAIL_ALIASES_PATH`, `RUNV_EMAIL_ALIASES_LOCK_PATH`, `RUNV_EMAIL_ALIAS_QUEUE_DIR`, `RUNV_EMAIL_ALIAS_DOMAIN`.

Mais detalhe dos comandos: [17-community-commands.md](17-community-commands.md).

### O que isto não faz

- Não cria mailbox.
- Não recebe email.
- Não envia email (além do stack transacional já existente).
- Não configura DNS.
- Não configura SPF/DKIM/DMARC.
- Não configura Postfix/Dovecot.
- Não configura Mailgun para aliases de membros.
- Não activa encaminhamento real automaticamente.

### Próximo passo futuro

Um script como `runv-email-provider-sync` poderá ler `email-aliases.json` e aplicar aliases no provedor real.

## Testes

- Existem testes em `email/tests/` (ex.: `test_mailgun_client.py`). Ver [14-smoke-tests-and-validation.md](14-smoke-tests-and-validation.md).

Próximo: [09-terminal-entre.md](09-terminal-entre.md).
