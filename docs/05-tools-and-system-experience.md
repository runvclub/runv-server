# Ferramentas e experiência de sistema

[← Índice](README.md)

## Script: `tools/tools.py`

**Função:** orquestrar no servidor Debian:

1. Pacotes APT listados em `tools/manifests/apt_packages.txt` (alias `chat` → metapacote `weechat`). O manifesto inclui **`weechat-curses`** explicitamente porque `tools.py` usa `apt-get install --no-install-recommends`: sem isso, o metapacote `weechat` pode satisfazer-se **só** com `weechat-headless` e o comando `chat` deixa de encontrar cliente interactivo (`weechat` / `weechat-curses` no PATH).
2. Cópia de `tools/bin/` para `/usr/local/bin` (`runv-help`, `runv-links`, `runv-status`, `chat`, `runv-profile`, `runv-finger`, `runv-who`, `runv-bulletin`, …) e de `tools/lib/runv_community.py` para `/usr/local/share/runv/lib/`.
3. MOTD dinâmico: `tools/motd/60-runv` → `/etc/update-motd.d/60-runv` (ver secção [MOTD](#motd-e-runv-help) abaixo).
4. Modelos para novas contas: `tools/skel/` → `/etc/skel/` (inclui `.plan`, `.project`, `.runv/profile.json`).
5. Drop-in SSH para utilizadores jailed: `tools/sshd/90-runv-jailed.conf` → `/etc/ssh/sshd_config.d/`.
6. Sudo administrativo para `pmurad-admin`: `tools/sudoers/90-runv-pmurad-admin` → `/etc/sudoers.d/`.
7. Reconciliação do jail SSH em membros existentes via `scripts/admin/perm1.py`.

**Princípios declarados no código:** Python stdlib; **sem `shell=True`** em subprocess.

## Execução

```bash
cd REPO/tools
sudo python3 tools.py --help
sudo python3 tools.py --dry-run --verbose   # simular
sudo python3 tools.py
```

Flags úteis: `--force`, `--skip-apt`, `--reconcile-existing-users` (ver `--help`).

## IRC / comando `chat`

- **Utilizador:** no servidor, use apenas o comando `chat` (wrapper em `/usr/local/bin/chat` após `tools/tools.py` ou `patches/patch_irc.py`). O cliente gráfico no terminal é `weechat` / `weechat-curses` (pacote `chat` no manifesto APT).
- **Por omissão** (após `patches/patch_irc.py`): ao correr `chat`, o WeeChat conecta no servidor interno **`runv`** (`irc.tilde.chat`, porta **6697**, **TLS ligado**), entra automaticamente em **`#runv`** e mostra a lista lateral de nicks quando o terminal tiver espaço utilizável. Outras redes que o utilizador adicionar manualmente **não** autoconectam por defeito (o patch desliga `autoconnect` nos outros servidores já existentes, sem apagar redes).
- **Provisionamento:** o patch corre com `weechat-headless -a -r '…' --stdout` (o `-a` evita auto-connect durante o batch). O launcher **`chat` não usa `-a`**. Novas contas Unix criadas com `scripts/admin/create_runv_user.py` invocam o patch automaticamente para esse utilizador. O `tools/tools.py --reconcile-existing-users` aplica o backfill IRC com `--force`.
- **Backfill / admin:** `sudo python3 patches/patch_irc.py --all-users --force` (ou `--user NOME --force`) reaplica servidor, autojoin em `#runv` e nicklist visível. Requer `weechat-headless` no sistema.

## Isolamento e permissões

- `pmurad-admin` fica explicitamente fora do grupo `runv-jailed` e recebe sudo administrativo via `/etc/sudoers.d/90-runv-pmurad-admin`.
- Membros normais continuam a usar o modelo `runv-jailed` + `ChrootDirectory /srv/jail/%u`, para não saírem das respetivas homes na shell SSH normal.
- `tools/tools.py` não altera contas já existentes por omissão. Se quiser reconciliar jail SSH e IRC em membros antigos, use `--reconcile-existing-users`.

## MOTD e `runv-help`

O ficheiro [`tools/motd/60-runv`](../tools/motd/60-runv) gera a mensagem de boas-vindas no login SSH (via `update-motd.d`). Secções:

| Secção | Conteúdo |
|--------|----------|
| Arte RUNV + tagline | Identidade visual alinhada ao site |
| Comandos úteis | `runv-help`, `runv-links`, `lynx`, `tmux`, `byobu`, `mutt`, `chat`, `runvers`, `runv-games` |
| Comunidade runv | `runv-profile`, `runv-finger`, `runv-who`, `runv-bulletin`, `runv-email-alias` |
| Últimos acessos recentes | Grelha 3×3 com até **9 membros distintos** (`last -w`); ordem = login mais recente de cada um; **não** é quem está online agora |

A ajuda completa está em `runv-help` (inclui a secção Comunidade e email de membro). Detalhes dos comandos: [17-community-commands.md](17-community-commands.md) e [08-email.md](08-email.md).

### Cache do MOTD (Debian)

O conteúdo mostrado no login costuma vir de `/run/motd.dynamic`, gerado por `run-parts /etc/update-motd.d/`. Em alguns sistemas o ficheiro é **actualizado em intervalo** (`motd-news`), não em cada login — a grelha de sessões pode parecer «congelada» até o cache refrescar.

**Diagnóstico (admin):**

```bash
stat /run/motd.dynamic
sudo /etc/update-motd.d/60-runv | tail -25
```

**Forçar refresh após alterar o script:**

```bash
cd /opt/runv-server/tools
sudo python3 tools.py --skip-apt --force
sudo run-parts /etc/update-motd.d > /run/motd.dynamic
```

Se o MOTD continuar desactualizado entre logins, rever `/etc/default/motd-news` na VPS (intervalo ou desactivar cache), conforme a política do servidor.

### `runv-who` e `users.json`

Para membros listarem utilizadores sem varrer `/home` (e sem erros em homes inacessíveis), o ficheiro canónico deve ser legível pelo grupo `runv-members`:

```bash
sudo chown root:runv-members /var/lib/runv/users.json
sudo chmod 640 /var/lib/runv/users.json
```

Próximo: [06-site-and-apache.md](06-site-and-apache.md).
