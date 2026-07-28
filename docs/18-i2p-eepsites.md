# Eepsites I2P (por membro)

[← Índice](README.md)

## Visão geral

Além de HTTP, Gopher, Gemini e Nex, cada membro tem um **eepsite** — um site
servido pela rede **I2P**, sem clearnet. É o quarto "espaço" pessoal da casa, no
mesmo espírito small web.

**Política:** por defeito, **ligado para todos**. Contas novas nascem com eepsite
(via `create_runv_user.py`, salvo `--no-i2p`); as contas antigas activam-se em bloco
com `setup_i2p.py --enable-all`. O fluxo opt-in por pedido (`runv-i2p request` +
`--enable-requested`) continua a existir para casos avulsos.

- Router: **i2pd** (C++, leve — pacote Debian), a correr como serviço `i2pd`.
- Um **server tunnel HTTP** por membro activado, com chaves próprias → um
  endereço **`.b32.i2p`** único.
- Todos os túneis apontam para **um único Apache** (`127.0.0.1:7980`) com
  *mass virtual hosting* (`mod_vhost_alias`, `VirtualDocumentRoot /home/%1/public_i2p`).
  Cada túnel envia `hostoverride = <user>.runv.i2p`, então o Apache serve o
  `~/public_i2p` do membro certo. Zero configuração Apache por utilizador.

Diferente de Gopher/Gemini/Nex: **não há porta clearnet de entrada**. A
acessibilidade vem da própria rede I2P (o i2pd trata do transporte, inclusive
atrás de NAT). Isto torna os eepsites mais privados por natureza — mas note-se
que hospedá-los aqui é *presença/reachability no I2P*, não hospedagem anónima
(o operador do runv.club correlaciona membro ↔ destino).

## Componentes

| Peça | Caminho |
|------|---------|
| Script admin | [`scripts/admin/setup_i2p.py`](../scripts/admin/setup_i2p.py) |
| Comando do membro | [`tools/bin/runv-i2p`](../tools/bin/runv-i2p) (instalado por `tools.py`) |
| Pasta do membro | `~/public_i2p/` (com `index.html` modelo) |
| Túnel i2pd | `/etc/i2pd/tunnels.conf.d/runv-i2p-<user>.conf` |
| Chaves i2pd | `/var/lib/i2pd/runv-i2p-<user>.dat` (geradas pelo i2pd) |
| vhost Apache | `/etc/apache2/sites-available/runv-i2p.conf` |
| Registo de endereços | `/var/lib/runv/i2p/addresses.json` (público, `.b32` partilhável) |
| Pedido do membro | `~/.runv/i2p.request` (marcador criado por `runv-i2p request`) |

## Instalação (uma vez)

No servidor (como root):

```bash
sudo python3 scripts/admin/setup_i2p.py --dry-run --verbose
sudo python3 scripts/admin/setup_i2p.py
```

Isto instala `i2pd` + `apache2`, activa `mod_vhost_alias`, escreve o vhost
(`configtest` antes de recarregar) e faz `enable --now` do i2pd. A infra base
**não** activa membros por si só.

## Activar os membros existentes (backfill)

```bash
sudo python3 scripts/admin/setup_i2p.py --enable-all
```

Activa o eepsite de **todos** os membros (exclui contas de serviço e `*-admin`).
Idempotente: reexecutar não duplica túneis nem muda endereços já emitidos.
Para um só membro: `--enable pablo willy`.

Ao activar (qualquer variante): cria `~/public_i2p` + `index.html`, escreve o
túnel, faz `reload-or-restart` do i2pd, espera as chaves, calcula o `.b32` e
regista-o.

## Membros novos (padrão)

`create_runv_user.py` já activa o eepsite na criação da conta (fase 3b), a par de
`public_html`/`gopher`/`gemini`/`nex`. Para criar sem I2P: `--no-i2p` (cria só
`~/public_i2p`, sem túnel).

## Ciclo por pedido (opcional)

Para activações avulsas ou se um dia a política voltar a opt-in:

```bash
runv-i2p request                                        # membro: cria ~/.runv/i2p.request
sudo python3 scripts/admin/setup_i2p.py --list-requests # admin: lista pendentes
sudo python3 scripts/admin/setup_i2p.py --enable-requested
```

## Publicar (membro)

```bash
runv-i2p show                 # mostra http://<b32>.b32.i2p/
$EDITOR ~/public_i2p/index.html
```

## Operação

```bash
sudo python3 scripts/admin/setup_i2p.py --list               # activos + endereços
sudo python3 scripts/admin/setup_i2p.py --refresh-addresses  # recalcula .b32 das chaves
sudo python3 scripts/admin/setup_i2p.py --disable pablo      # remove o túnel
```

`--disable` mantém as chaves (`.dat`) e o `~/public_i2p`, para o endereço ser o
**mesmo** se reactivar. Flags globais: `--dry-run`, `--verbose`, `--force`,
`--skip-install`.

## Notas e limites

- **Memória escala com o nº de túneis.** Para uma dúzia de membros é tranquilo;
  a natureza opt-in evita gastar recursos com quem não usa. Monitor:
  `http://127.0.0.1:7070` (consola i2pd) e `systemctl status i2pd`.
- **Endereços são feios** (`.b32.i2p`, 52 chars). Nomes amigáveis `.i2p` exigem
  registo em address book / jump service — fora do âmbito deste script.
- **Primeiro acesso demora**: após activar, o eepsite pode levar minutos a ficar
  acessível enquanto o i2pd constrói túneis e publica o LeaseSet.
- O `.b32` é **público** (feito para partilhar); o registo e o ficheiro
  `~/public_i2p/.eepsite-address` são `0644` de propósito.

## Testes

```bash
cd REPO
python3 -m compileall -q scripts/admin/setup_i2p.py tools/bin/runv-i2p
python3 -m unittest tests.test_i2p_b32 -v   # deriva .b32 (Unix)
```

Próximo: [15-glossary-and-reference.md](15-glossary-and-reference.md).
