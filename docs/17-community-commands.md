# Comandos comunitários

[← Índice](README.md)

## Visão geral

Estes comandos dão mais vida pubnix ao servidor runv.club:

- **perfil local** (`runv-profile`) — ficheiros em `~/.runv/profile.json`, `~/.plan` e `~/.project`;
- **finger moderno** (`runv-finger`) — ver o perfil público de outro membro;
- **listagem de membros** (`runv-who`) — quem está na comunidade e sinais de actividade;
- **mural comunitário** (`runv-bulletin`) — mensagens curtas partilhadas no terminal.

São instalados por [`tools/tools.py`](../tools/tools.py) em `/usr/local/bin` (junto com `runv-help`, `chat`, etc.). A biblioteca partilhada fica em `/usr/local/share/runv/lib/runv_community.py`.

No login SSH, o MOTD ([`tools/motd/60-runv`](../tools/motd/60-runv)) e `runv-help` listam estes comandos na secção **Comunidade runv**. Ver também [05-tools-and-system-experience.md](05-tools-and-system-experience.md#motd-e-runv-help).

Não expõem email, chave pública nem fingerprint de `/var/lib/runv/users.json` (excepto `runv-who`, que usa só a lista de usernames em `users.json` quando legível).

## `runv-profile`

### O que faz

Gerencia o perfil local público:

- `~/.runv/profile.json`
- `~/.plan`
- `~/.project`

### Exemplos

```bash
runv-profile init
runv-profile show
runv-profile path
```

### Arquivos criados

| Caminho | Descrição |
|---------|-----------|
| `~/.runv/profile.json` | Nome, bio, local, links, interesses |
| `~/.plan` | Plano actual (texto livre) |
| `~/.project` | Projecto actual (texto livre) |

### Permissões esperadas

| Caminho | Modo |
|---------|------|
| `~/.runv` | `755` |
| `~/.runv/profile.json` | `644` |
| `~/.plan` | `644` |
| `~/.project` | `644` |

### Observações

- `init` **não sobrescreve** ficheiros existentes.
- Não guarde dados sensíveis no perfil (são legíveis por outros membros via `runv-finger`).
- Contas antigas sem estes ficheiros podem correr `runv-profile init` uma vez.

---

## `runv-finger`

### O que faz

Mostra o perfil público de outro membro (estilo `finger`).

### Exemplo

```bash
runv-finger pablo
```

### Dados exibidos

- `~/.runv/profile.json` (campos públicos)
- `~/.plan`
- `~/.project`
- existência e última actualização de `~/public_html/index.html` (como `Home: /~USER/`)

### Segurança

- Não mostra email.
- Não mostra chave pública.
- Não mostra fingerprint.
- Cada ficheiro é lido com limite de **16 KiB**.

---

## `runv-who`

### O que faz

Lista membros da runv.club com indícios de actividade (homepage, `.plan`, `.project`).

### Exemplos

```bash
runv-who
runv-who --active
runv-who --limit 20
runv-who --json
```

### Fontes de dados

**Preferencial:** `/var/lib/runv/users.json` (apenas usernames; formatos suportados: lista de objectos com `username`, objecto com chaves = usernames, ou `{ "users": [ ... ] }`).

**Fallback:** directórios em `/home/` cujo nome passa na regex de username.

Se `users.json` existir mas for inválido, aparece um aviso e usa-se `/home`.

### Campos exibidos

| Campo | Significado |
|-------|-------------|
| `username` | Nome Unix |
| `homepage` | Sempre `/~USER/` |
| `has_homepage` | Existe `~/public_html/index.html` |
| `homepage_mtime` | ISO UTC da última modificação da homepage, ou `null` |
| `has_plan` | `.plan` existe e não está vazio |
| `has_project` | `.project` existe e não está vazio |

### Ordenação

1. Membros com homepage, por data da homepage (mais recente primeiro).
2. Membros sem homepage, por ordem alfabética.

Com `--active`, só entram quem tem homepage **ou** `.plan` **ou** `.project`.

### JSON

`--json` imprime um array JSON só com os campos acima — útil para integração futura com site, Garden, Gotchi ou outros scripts.

---

## `runv-bulletin`

### O que faz

Mural comunitário simples em terminal (uma linha JSON por post).

### Exemplos

```bash
runv-bulletin
runv-bulletin list
runv-bulletin post "Hoje configurei meu gopher"
runv-bulletin --limit 10
runv-bulletin --json
```

Sem subcomando, equivale a `list`.

### Arquivos usados

| Caminho | Função |
|---------|--------|
| `/var/lib/runv/bulletin/posts.ndjson` | Posts (NDJSON) |
| `/var/lib/runv/bulletin/posts.lock` | Lock `flock` em escritas |

Testes locais:

```bash
export RUNV_BULLETIN_PATH=/tmp/runv-bulletin/posts.ndjson
```

### Formato

Uma linha JSON por post, por exemplo:

```json
{"id":"20260519T120000Z-pablo-a1b2c3","username":"pablo","created_at":"2026-05-19T12:00:00Z","body":"Hoje configurei meu gopher"}
```

O username em `post` vem sempre do utilizador Unix actual (`getpwuid`); não se aceita username por argumento.

### Permissões

O directório global precisa permitir escrita pelos membros. Sugestão operacional (ajuste o grupo se o vosso não for `runv`):

```bash
sudo mkdir -p /var/lib/runv/bulletin
sudo touch /var/lib/runv/bulletin/posts.ndjson
sudo touch /var/lib/runv/bulletin/posts.lock
sudo chgrp -R runv /var/lib/runv/bulletin
sudo chmod 2775 /var/lib/runv/bulletin
sudo chmod 664 /var/lib/runv/bulletin/posts.ndjson /var/lib/runv/bulletin/posts.lock
```

Sem permissão de escrita, `post` mostra mensagem clara — **não** há fallback para `/tmp`.

---

## Instalação

No servidor (clone em `REPO`):

```bash
cd REPO/tools
sudo python3 tools.py --dry-run --verbose
sudo python3 tools.py
```

Verificar:

```bash
which runv-profile runv-finger runv-who runv-bulletin runv-email-alias runv-admin-email-alias
ls -l /usr/local/share/runv/lib/runv_community.py /usr/local/share/runv/lib/runv_email_aliases.py
```

Novas contas recebem modelos em `/etc/skel` (`.plan`, `.project`, `.runv/profile.json`) após `tools.py`.

---

## Testes manuais rápidos

```bash
runv-profile init
runv-profile show
runv-finger "$USER"
runv-who
runv-who --json

mkdir -p /tmp/runv-bulletin-test
export RUNV_BULLETIN_PATH=/tmp/runv-bulletin-test/posts.ndjson
runv-bulletin post "primeiro teste do mural"
runv-bulletin
runv-bulletin --json
```

Sintaxe Python (repo):

```bash
cd REPO
python3 -m compileall -q tools
```

---

## `runv-email-alias`

### O que faz

Permite pedir um alias de email fixo `username@runv.club` que, após aprovação admin, deve encaminhar para um email externo.

- Não cria mailbox no servidor.
- Não activa o encaminhamento automaticamente.
- O membro só indica o email de destino; o nome do alias segue o username Unix.

### Exemplos

Na sessão SSH do **membro** (sem `sudo`):

```bash
runv-email-alias request usuario@example.org
runv-email-alias status
runv-email-alias cancel
```

Requisito: o utilizador tem de pertencer ao grupo `runv-members` (contas criadas com `create_runv_user.py`). Contas só de administração do servidor não usam este comando.

Política, ficheiros em `/var/lib/runv/` e setup: [08-email.md](08-email.md).

---

## `runv-admin-email-alias`

### O que faz

Comando **root** para listar pedidos, aprovar ou rejeitar aliases, e actualizar `email-aliases.json` localmente. Não chama Mailgun nem configura DNS.

### Exemplos

```bash
sudo runv-admin-email-alias pending
sudo runv-admin-email-alias list
sudo runv-admin-email-alias approve pablo
sudo runv-admin-email-alias sync
sudo runv-admin-email-alias reject pablo --reason "email destino inválido"
```

Sync Postfix (membros, não Mailgun): [08-email.md](08-email.md) e `scripts/admin/discover_mail_stack.py`.

Setup inicial da fila e permissões:

```bash
sudo python3 scripts/admin/setup_email_aliases.py
sudo python3 scripts/admin/setup_email_aliases.py --add-existing-users
```

---

## Próximos passos futuros

Possíveis evoluções (fora do âmbito actual):

- `runv-admin bulletin hide/delete` (moderação);
- feed público do mural no site;
- integração com Garden / Gotchi;
- backfill admin para membros existentes.

Próximo: [15-glossary-and-reference.md](15-glossary-and-reference.md).
