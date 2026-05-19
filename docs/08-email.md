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

- **Não** substitui a instalação Postfix/Dovecot/Roundcube no servidor (isso é operação de sistema).
- **Não** usa Mailgun para correio de membros.

## Dois canais de email (não misturar)

| Canal | Função | Config no servidor |
|-------|--------|-------------------|
| **Mailgun** | Transacional / admin (`entre`, boas-vindas, avisos) | `/etc/runv-email.json` |
| **MTA local** | Correio `@runv.club` para membros (caixa, webmail, encaminhamento) | Postfix + Dovecot + Roundcube (fora deste repo) |

O Mailgun **não** deve receber pedidos de alias `username@runv.club → Gmail`. Isso é papel do **Postfix** (ou mapa virtual equivalente) já instalado na VPS.

## Aliases de email para membros

O fluxo runv regista pedidos e aprovações em JSON. O encaminhamento real pode ser aplicado no Postfix com `runv-admin-email-alias sync` quando `/etc/runv-member-mail.json` estiver activo (ver abaixo).

Um membro pode pedir um alias fixo:

`username@runv.club` → email externo de destino

Por omissão o membro pede no terminal, o admin aprova, e o registo fica em JSON. Com sync Postfix configurado, o encaminhamento no MTA local pode ser automático após `approve` ou via `sync`.

### Membro

**Sem `sudo` e sem root.** O membro corre os comandos na própria sessão SSH (conta Unix da comunidade, ex. `pmurad`). O sistema usa o username dessa sessão; contas de operador/admin (ex. `pmurad-admin`) **não** estão em `runv-members` e não podem pedir alias por design.

```bash
runv-email-alias request usuario@example.org
runv-email-alias status
runv-email-alias cancel
```

- `status` lê `/var/lib/runv/email-aliases.json` (modo `640`, grupo `runv-members`).
- `request` / `cancel` escrevem só na fila `email-alias-queue/` (modo `2770`, mesmo grupo).
- Aprovação e alteração do JSON activo são sempre **admin** (`runv-admin-email-alias` como root).

O alias é sempre `username@runv.club` (username Unix do utilizador que corre o comando). Não é possível escolher outro nome de alias.

### Admin

```bash
sudo runv-admin-email-alias pending
sudo runv-admin-email-alias list
sudo runv-admin-email-alias approve pablo
sudo runv-admin-email-alias approve pablo --sync-mail
sudo runv-admin-email-alias sync
sudo runv-admin-email-alias reject pablo --reason "email destino inválido"
```

### Inventário e sync Postfix (MTA local)

Na VPS, antes de activar sync:

```bash
sudo python3 scripts/admin/discover_mail_stack.py
```

Copiar e editar o exemplo:

```bash
sudo cp email/config/runv-member-mail.example.json /etc/runv-member-mail.json
# enabled: true após validar postconf virtual_alias_maps
sudo python3 scripts/admin/sync_member_email_aliases.py --dry-run
sudo runv-admin-email-alias sync
```

Na vossa VPS o Postfix usa **`mysql:/etc/postfix/mysql-virtual-alias-maps.cf`** — use backend `postfix-mysql` (não adicione mapa hash paralelo).

```bash
sudo python3 scripts/admin/inspect_postfix_mysql_aliases.py
sudo cp email/config/runv-member-mail.example.json /etc/runv-member-mail.json
# editar enabled + colunas/tabela se o inspect sugerir
sudo runv-admin-email-alias sync
```

O sync faz UPSERT na tabela de aliases e `reload postfix`. **Não** altera Mailgun.

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
- Não configura Roundcube/Dovecot directamente (só mapa virtual Postfix quando sync activo).

### Próximo passo futuro

Suporte a backends além de `postfix-hash` (ex. SQL já usado pelo servidor) após mapear o que `discover_mail_stack.py` reportar.

## Testes

- Existem testes em `email/tests/` (ex.: `test_mailgun_client.py`). Ver [14-smoke-tests-and-validation.md](14-smoke-tests-and-validation.md).

Próximo: [09-terminal-entre.md](09-terminal-entre.md).
