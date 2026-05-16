# Reparar usuários

[← Índice](README.md)

Use esta página quando um membro existe no sistema, mas a home ficou incompleta ou com permissões erradas. Sintomas comuns:

- `https://runv.club/~USER/` mostra `Index of /~USER`;
- falta `~/public_html/index.html`;
- faltam `~/public_gopher/gophermap` ou `~/public_gemini/index.gmi`;
- a home está com dono `root:root` após remoção de jail antiga;
- o provisionamento foi interrompido depois do `adduser`.

## Ferramenta canônica

O reparador é:

```bash
sudo python3 REPO/scripts/admin/repair_user.py --help
```

Ele é conservador:

- cria apenas diretórios e arquivos esperados quando estão ausentes;
- não sobrescreve `index.html`, `gophermap` ou `index.gmi` existentes;
- corrige dono e modo da home e dos artefatos padrão;
- não faz `chown -R`;
- não toca em `/var/vmail`, Dovecot, Roundcube, Maildir ou qualquer parte do email.

## Reparar um usuário

Sempre comece com `--dry-run`:

```bash
cd /opt/runv-server
sudo python3 scripts/admin/repair_user.py --user USER --dry-run --verbose
```

Se o plano estiver correto:

```bash
sudo python3 scripts/admin/repair_user.py --user USER
```

O script garante:

| Caminho | Modo | Dono |
|---------|------|------|
| `/home/USER` | `755` | `USER:USER` |
| `/home/USER/.ssh` | `700` | `USER:USER` |
| `/home/USER/.ssh/authorized_keys`, se existir | `600` | `USER:USER` |
| `/home/USER/public_html` | `755` | `USER:USER` |
| `/home/USER/public_html/index.html` | `644` | `USER:USER` |
| `/home/USER/public_gopher` | `755` | `USER:USER` |
| `/home/USER/public_gopher/gophermap` | `644` | `USER:USER` |
| `/home/USER/public_gemini` | `755` | `USER:USER` |
| `/home/USER/public_gemini/index.gmi` | `644` | `USER:USER` |

Se `authorized_keys` estiver ausente, o script avisa e não cria uma chave falsa. A chave pública precisa ser recuperada do pedido original ou instalada por outro fluxo administrativo.

## Reparar todos os candidatos

Para verificar usuários de `/var/lib/runv/users.json` e contas candidatas em `/home`:

```bash
sudo python3 scripts/admin/repair_user.py --all-users --dry-run --verbose
```

Para aplicar:

```bash
sudo python3 scripts/admin/repair_user.py --all-users
```

O modo `--all-users` ignora contas reservadas como `root`, `entre`, `pmurad-admin`, `www-data` e `vmail`.

## Validação

Depois do reparo:

```bash
sudo ls -la /home/USER
sudo ls -la /home/USER/public_html
curl -I https://runv.club/~USER/
```

O navegador deve deixar de mostrar `Index of /~USER` quando `public_html/index.html` existir. Se o Apache ainda listar o diretório, confirme:

```bash
sudo stat /home/USER /home/USER/public_html /home/USER/public_html/index.html
sudo journalctl -u apache2 --since "10 minutes ago"
```

## Quando não usar

Não use `repair_user.py` para:

- trocar chave SSH;
- recriar usuário removido;
- corrigir quota;
- reparar email local;
- mexer em `/var/vmail`;
- refazer jail SSH legada.

Para chave SSH, use o fluxo de atualização de usuário. Para quota, use `create_runv_user.py` / `update_user.py` conforme o caso. Para email local, preserve a regra operacional: o RunV não deve alterar permissões de `/var/vmail`.

Próximo: [Glossário e referência](15-glossary-and-reference.md).
