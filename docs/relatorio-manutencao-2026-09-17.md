# Relatório de manutenção — 17/09/2026

[← Índice](README.md)

Registro de uma sessão de manutenção em `srv1.runv.club`: auditoria de acessos, restauro do acesso de um membro, correção de logging e proteção anti-varredura. Documento de histórico operacional, no mesmo formato de [review-email-aliases-signoff.md](review-email-aliases-signoff.md).

| Campo | Valor |
|---|---|
| Data | 2026-09-17 |
| Máquina | `srv1.runv.club` — Debian 13, Contabo, 6 vCPU / 12 GB / 394 GB |
| Escopo | acessos, conta `kirihito`, logrotate, journald, vhost `garden`, fail2ban |
| Executado por | pmurad-admin |
| Commit | `⟨CONFIRMAR: git rev-parse --short HEAD⟩` |

> **Marcadores `⟨CONFIRMAR⟩`.** Os valores que só existem na máquina estão marcados assim, com o comando que os resolve ao lado. Quem tiver acesso ao servidor substitui o marcador pela saída. Um marcador por preencher significa que o número ainda não foi verificado — não que seja aproximado.

---

## Resumo executivo

Quatro problemas estavam ativos nesta máquina sem aparecer em lado nenhum a não ser nos logs:

1. **Um membro aprovado esteve quatro meses sem conseguir entrar.** A conta `kirihito` ficou sem `authorized_keys` a partir de 16 de maio, por causa de alguma rotina de manutenção que ainda não foi identificada. Nunca chegou a fazer login: zero registros no `wtmp`, que cobre desde 22 de março.
2. **O fail2ban nunca bloqueou nada.** As quatro jails estavam configuradas com `banaction = nftables` numa máquina sem o comando `nft`. 1.403 "bans" de SSH registrados que nunca existiram no kernel.
3. **O `logrotate` nunca esteve instalado.** Os arquivos de configuração vinham com os pacotes das aplicações; o binário não. 145 MB de log acumulado desde março.
4. **O `garden` respondia `200 OK` a qualquer caminho**, incluindo `/.env` e `/.git/config`.

Os quatro foram corrigidos ou revertidos nesta sessão.

### O que a evidência sustenta, e o que não sustenta

Não há indício de invasão nem de vazamento nos registros que ainda existem. A força dessa afirmação muda conforme o serviço, e a diferença importa:

| Superfície | Janela de evidência | O que se pode afirmar |
|---|---|---|
| HTTP (Apache) | contínua desde março — os logs nunca rodaram, que é o próprio bug nº 3 | O `garden` devolvia 735 bytes do `index.html` a todos os caminhos sondados; nenhum arquivo de segredo foi servido. Afirmação sólida. |
| SSH, IMAP, SMTP | ~7 dias — journald limitado a `SystemMaxUse=300M` | Nada de anormal na semana observada. Os meses anteriores **não podem ser examinados**: o histórico foi descartado pela rotação do journal. |
| Gopher, Nex | ~7 dias, mesma limitação — nenhum dos dois escreve arquivo de log próprio | Só a semana observada. |

Com o fail2ban decorativo desde a instalação, a máquina esteve sem proteção contra força bruta em SSH, IMAP e SMTP durante todo esse período. O que se sabe é que não há rastro de sucesso na janela visível. Não é o mesmo que dizer que não aconteceu nada em julho.

---

## Como estes números foram obtidos

O relatório anterior dizia "já descontando bots, scanners e monitorização" sem dizer como. Esta seção existe para que qualquer tabela abaixo possa ser refeita no mês que vem e dar o mesmo resultado.

### Onde cada protocolo escreve

| Protocolo | Caminho | Rotação | Observação |
|---|---|---|---|
| HTTP (Apache) | `${APACHE_LOG_DIR}/<tag>-access.log` — ver [`site/genlanding.py`](../site/genlanding.py) | nenhuma até 17/09 | Por isso existe série contínua desde março. |
| Gemini (molly-brown) | `/var/lib/molly-brown/<instância>-access.log` — ver [`setup_alt_protocols.py`](../scripts/admin/setup_alt_protocols.py) | nenhuma | Não fica em `/var/log/`: o drop-in `LogsDirectory` foi removido de propósito, porque empurrava os logs para `/var/log/private/` e quebrava o arranque do Molly. |
| Gopher (gophernicus) | nenhum arquivo | journald | Roda por socket systemd; `/etc/default/gophernicus` não tem diretiva de log. |
| Nex (nexd) | nenhum arquivo | journald | [`nexd.py`](../scripts/admin/nexd.py) loga para stderr, uma linha por pedido. |
| `entre` (SSH) | `/var/log/runv/entre.log` | — | Ver [09-terminal-entre.md](09-terminal-entre.md). |
| Provisionamento | `/var/log/runv-user-provision.log` | — | Escrito por [`create_runv_user.py`](../scripts/admin/create_runv_user.py). |

**Consequência direta:** as tabelas de HTTP e Gemini cobrem de março a setembro. As de Gopher e Nex cobrem **a semana observada**, e só. Qualquer frase do tipo "em todo o histórico" sobre esses dois protocolos é insustentável e foi removida deste relatório.

### Filtro aplicado

Um acesso conta como visita humana quando:

- o status é `200` ou `304`;
- o caminho não é asset estático (`css`, `js`, `woff2`, `svg`, `png`, `jpg`, `ico`, `map`, `json`, `xml`, `txt`);
- o User-Agent não contém `bot`, `crawl`, `spider`, `slurp`, `scrapy`, `curl`, `wget`, `python-requests`, `zabbix`, `uptime`, `headless`;
- o IP de origem não é `207.180.232.129` (monitoração SNMP do provedor).

### Comandos

Tabela de HTTP por mês (pageviews e IPs únicos):

```bash
zcat -f /var/log/apache2/runv.club-access.log* \
| grep -vEi 'bot|crawl|spider|slurp|scrapy|curl|wget|python-requests|zabbix|uptime|headless' \
| grep -v '^207\.180\.232\.129 ' \
| awk '$9 ~ /^(200|304)$/ && $7 !~ /\.(css|js|woff2?|svg|png|jpe?g|ico|map|json|xml|txt)$/ {
    split($4, d, "/"); split(d[3], y, ":"); m = d[2] "/" y[1]
    hits[m]++; seen[m SUBSEP $1] = 1
  }
  END {
    for (k in seen) { split(k, p, SUBSEP); ips[p[1]]++ }
    for (m in hits) printf "%s\t%d\t%d\n", m, hits[m], ips[m]
  }' | sort
```

Páginas mais vistas, mesma base:

```bash
zcat -f /var/log/apache2/runv.club-access.log* \
| grep -vEi 'bot|crawl|spider|slurp|scrapy|curl|wget|python-requests|zabbix|uptime|headless' \
| awk '$9 ~ /^(200|304)$/ && $7 ~ /\/$/ {print $7}' \
| sort | uniq -c | sort -rn | head -20
```

Origem do tráfego (campo Referer do formato `combined`):

```bash
zcat -f /var/log/apache2/runv.club-access.log* \
| awk -F'"' '$4 != "-" {print $4}' \
| awk -F/ '{print $3}' | sort | uniq -c | sort -rn | head -20
```

Gemini — o formato do log do molly-brown **não** é o `combined` do Apache. Confirmar antes de adaptar o awk:

```bash
head -3 /var/lib/molly-brown/*-access.log    # ⟨CONFIRMAR: formato e posição dos campos⟩
```

Gopher e Nex, dentro da janela do journal:

```bash
journalctl -u gophernicus@.service --since '7 days ago' --no-pager
journalctl -u runv-nexd --since '7 days ago' --no-pager
```

### Por que os números brutos enganam

O `garden` aparentava 59 mil acessos em setembro. Quase tudo era varredura contra um vhost que respondia `200 OK` a qualquer caminho (ver 2.4). Ler o total do Apache sem filtro não mede audiência nenhuma; mede quantos scanners passaram.

---

## Parte 1 — O runv tem acesso?

Tem. O que não tem é atividade de membros.

### Site (números produzidos pelos comandos acima)

| Mês | Pageviews | IPs únicos |
|---|---:|---:|
| Março | 3.316 | 970 |
| Abril | 1.962 | 769 |
| Maio | 2.384 | 837 |
| Junho | 1.843 | 728 |
| Julho | 4.139 | 1.594 |
| Agosto | 4.258 | 1.478 |
| Setembro (17 dias) | 2.657 | 669 |

Média de ~50 visitantes únicos por dia em setembro, estável. Depois da home, as páginas mais vistas são `/news/`, `/wiki/`, `/junte-se/` e `/faq/`. É gente lendo sobre a comunidade e sobre como entrar.

### Gemini

| Mês | Requisições | IPs únicos |
|---|---:|---:|
| Março | 84 | 10 |
| Abril | 159 | 17 |
| Maio | 305 | 92 |
| Junho | 653 | 148 |
| Julho | 704 | 152 |
| Agosto | 729 | 167 |
| Setembro (17 dias) | 402 | 101 |

Crescimento de 10 para 167 IPs únicos em cinco meses. É a curva mais saudável do projeto.

### Gopher e Nex

Ambos limitados à janela de sete dias do journal, pelas razões da seção de metodologia.

- **Gopher:** ~47 IPs distintos na semana observada. Movimento real, modesto.
- **Nex (porta 1900):** nenhum cliente legítimo na semana observada. O que chegou foram tentativas de handshake de TLS, SMB e MSSQL, típicas de varredura de portas. Para afirmar qualquer coisa sobre meses anteriores seria preciso um log persistente, que o `nexd` não escreve.

### De onde vêm

Google (262), Bing (84), DuckDuckGo (76). Entre os referrers humanos: `pablo.ooo` (43), `soledade.city` (28), `pmurad.lol` (14), `rubylugarden.com` (6).

### Os membros

A conta `entre` **não** entra nesta contagem: é a conta de sistema do fluxo de cadastro, nome reservado em [`create_runv_user.py`](../scripts/admin/create_runv_user.py) e [`entre_core.py`](../terminal/entre_core.py), e explicitamente excluída da jail em [`runv_jail.py`](../scripts/admin/runv_jail.py). Contá-la como membro inflaciona o problema.

| Membro | Arquivos publicados | Última alteração | Acessos à página (IPs únicos) |
|---|---:|---|---:|
| pmurad | 11 (html) + placeholders | 27/mar | 753 |
| willy | 4 (html) + placeholders | 30/mar | 52 |
| kirihito | só placeholders | 16/mai | 28 |
| will | só placeholders | 23/mar | 27 |
| marcelo | só placeholders | 23/mar | 24 |

São **cinco** contas de membro. Uma publica, uma publicou pouco, três têm apenas os placeholders gerados no provisionamento — e uma dessas três (`kirihito`) esteve tecnicamente impedida de entrar desde maio.

Cinco contas não sustentam um diagnóstico estatístico de conversão. O que há é um sinal, e o sinal é forte o bastante para agir: quatro pessoas aprovadas, nenhuma publicando.

**Logins SSH:** desde julho, o único login de outro membro foi `entre`, em 1 de julho, a partir de `::1` (localhost). Todo o resto é a conta de administração.

**Correio:** existe uma caixa em `/var/vmail/runv.club/`, a `admin`, com 15 mensagens. O servidor de mail próprio (postfix, dovecot, rspamd) não é usado por ninguém.

---

## Parte 2 — O que foi feito

### 2.1 Acesso do kirihito restaurado

**Pedido:** e-mail de Josué Ravi Dantas Freire (`kirihito@cock.li`), 7 de setembro, pedindo substituição da chave SSH.

**Verificação feita antes de aplicar:**

- mensagem localizada em `/var/vmail/runv.club/admin/Maildir/cur/`;
- entregue por `mail.cock.li` (37.120.193.124), o MX real do domínio — não foi spoof via relay aberto;
- `DKIM-Signature: d=cock.li` presente, cobrindo o header `From`;
- `X-Mailer: aerc 0.22.0`, cliente de terminal, coerente com o perfil;
- remetente idêntico ao e-mail do cadastro em `/var/lib/runv/entre-queue/approved/560b7a86-….json`.

**Descoberta relevante:** a conta estava sem chave nenhuma desde 16 de maio, e não por culpa dele. O log de provisionamento mostra a fase 2 (`SSH authorized_keys`) concluída em 14/mai. Em 16/mai às 18:44, alguma rotina recriou `~/.ssh` e os três diretórios `public_*` com placeholders, e o `authorized_keys` desapareceu. Ele é o único dos cinco membros sem chave. Nunca conseguiu entrar.

O "perdi a minha chave" da mensagem dele é a leitura de quem nunca conseguiu entrar e presume ter errado alguma coisa.

**Aplicado** pela ferramenta do projeto, não à mão:

```bash
sudo python3 REPO/scripts/admin/update_user.py \
     -u kirihito --ssh-replace-file <arquivo>
```

Resultado verificado: `authorized_keys` com modo `600`, `~/.ssh` com `700`, ambos com dono `kirihito`, fingerprint `SHA256:WrTOy5PRvjFhAVm90xeg+JJBOTK14G2F39o12UGUeLA` registrado em `users.json`, `members.json` público regerado.

Sobre a conta estar "igual às que funcionam": um membro criado só por `create_runv_user.py` não entra em nenhum grupo secundário. O grupo `runv-members` existe, mas vem de [`setup_email_aliases.py`](../scripts/admin/setup_email_aliases.py) e só é atribuído por `--add-existing-users`; `runv-jailed` vem de [`runv_jail.py`](../scripts/admin/runv_jail.py) e é opt-in (`--with-jail`). A comparação precisa nomear o grupo e a origem:

```bash
id kirihito && id willy && id will     # ⟨CONFIRMAR: grupos de cada um⟩
```

**Risco residual, declarado:** tudo o que foi verificado prova controle da caixa de correio, não da pessoa. Quem tivesse tomado o `kirihito@cock.li` passaria nos mesmos testes, e o cock.li é provedor anônimo, sem recuperação. Como o cadastro do runv ancora identidade no e-mail, isto é praticamente o teto do que se consegue verificar por esse canal. Ver a sugestão de segundo fator na Parte 4.

### 2.2 `logrotate` — causa raiz

O diagnóstico óbvio seria "o logrotate está mal configurado". Não estava: `/etc/logrotate.d/apache2` estava correto, com `daily` e `rotate 14`. O pacote `logrotate` nunca tinha sido instalado — os arquivos de configuração vêm com os pacotes das aplicações, o binário não.

- pacote instalado, `logrotate.timer` ativo (execução diária, 00:06);
- primeira rotação forçada: `runv.club-access.log` (37 MB) e `garden.runv.club-access.log` (78 MB) passaram a `.1`, logs novos a zero;
- a compressão acontece na rotação seguinte por causa do `delaycompress`, que evita que o Apache escreva num arquivo em compressão.

### 2.3 Retenção do journald

O journald estava em `SystemMaxUse=300M`. Com o volume de ruído dos scanners, isso cobria cerca de sete dias, e já tinha custado o histórico de Gopher, dovecot e postfix. É também a razão de os limites de evidência declarados no resumo serem os que são.

Criado `/etc/systemd/journald.conf.d/runv-retention.conf`:

```ini
[Journal]
SystemMaxUse=3G
SystemKeepFree=20G
MaxRetentionSec=90day
MaxFileSec=1day
```

Feito como drop-in, não editando o arquivo principal, para sobreviver a atualizações do pacote. O disco tem 371 GB livres.

### 2.4 `garden.runv.club` — fim do `200 OK` para tudo

O vhost tinha o fallback clássico de SPA: qualquer caminho que não fosse arquivo ou diretório servia `index.html`. Resultado: `/.env`, `/.git/config` e `/wp-admin` respondiam `200 OK`.

Nada vazava — a resposta eram 735 bytes do `index.html` da aplicação. Mas tinha três custos reais: sinalizava aos scanners que havia algo ali, envenenava as métricas (é a origem dos 59 mil acessos aparentes de setembro) e era semanticamente errado.

Adicionadas duas regras **antes** do fallback, em ambos os vhosts (`:80` e `:443`):

```apache
RewriteCond %{REQUEST_URI} !^/\.well-known/
RewriteRule "(^|/)\.[^/]" - [R=404,L]
RewriteRule "\.(php|phtml|asp|aspx|jsp|cgi|pl|sh|sql|bak|old|swp|ini)$" - [R=404,L]
```

Abordagem conservadora de propósito: só devolve 404 ao que comprovadamente não é rota de SPA. `/admin`, `/login` e `/dashboard` continuam a cair no fallback, caso sejam rotas client-side legítimas.

Verificado após `reload`:

| Caminho | Antes | Depois |
|---|---|---|
| `/` | 200 | 200 |
| `/favicon.svg` | 200 | 200 |
| `/admin` | 200 | 200 |
| `/.well-known/acme-challenge/…` | 200 | 200 |
| `/.env` | 200 | 404 |
| `/.env.production` | 200 | 404 |
| `/.git/config` | 200 | 404 |
| `/index.php` | 200 | 404 |

O `.well-known` foi testado explicitamente: se quebrasse, o certbot deixaria de renovar os certificados.

Os outros vhosts (`runv.club`, `square`) já respondiam 404 corretamente. O `webmail` devolve 403 a dotfiles e 200 a `/index.php`, o que está certo — o Roundcube é PHP de verdade.

### 2.5 fail2ban — o achado mais grave

Ao testar a jail nova, o ban aparecia no `fail2ban-client status` mas não existia no kernel:

```
/bin/sh: 1: nft: not found
```

As quatro jails (`sshd`, `postfix`, `postfix-sasl`, `dovecot`) estavam configuradas com `banaction = nftables` numa máquina onde o comando `nft` não estava instalado.

Consequências:

- 7.092 erros `nft: not found` acumulados, que explicam os 17 MB do `fail2ban.log`;
- o `sshd` registrou 1.403 bans que nunca bloquearam nada;
- proteção contra força bruta inexistente em SSH, IMAP e SMTP desde a instalação, com um fail2ban decorativo dando falsa segurança.

**Corrigido:** pacote `nftables` instalado.

Cuidado tomado: o `nftables.service` ficou `disabled`/`inactive` de propósito. Se arrancasse, carregaria `/etc/nftables.conf` e poderia atropelar as regras do UFW. Confirmado antes e depois que o UFW mantém as mesmas 114 regras e que a regra `161/udp ALLOW 207.180.232.129` (monitoração SNMP) está intacta.

Verificação de que o ban chega ao kernel:

```
table inet f2b-table {
        set addr-set-sshd {
                type ipv4_addr
                elements = { 101.47.15.26, 139.59.36.109 }
        }
```

Dois atacantes reais bloqueados em SSH, pela primeira vez de fato. Zero erros de `nft` desde o restart.

### 2.6 Jail anti-varredura nova

Criados `/etc/fail2ban/filter.d/runv-webscan.conf` e `/etc/fail2ban/jail.d/runv-webscan.conf`.

Detecta sondagem a arquivos de segredos (`.env`, `.git`, `.aws`, `.ssh`), painéis inexistentes (WordPress, phpMyAdmin, `/actuator`, `/solr`) e extensões de script que este servidor não roda.

Decisões de desenho:

- `backend = auto`, porque estes são logs em arquivo; o `[DEFAULT]` da máquina usa `systemd`;
- o vhost do webmail ficou deliberadamente fora do `logpath` — o Roundcube serve `.php` legítimo e seria banido;
- herda `ignoreip` de `[DEFAULT]`, que inclui `207.180.232.129`. Confirmado ativo na jail. **Não quebrar esta herança**, ou a monitoração é banida;
- `maxretry = 2`, `findtime = 10m`, `bantime = 1w`.

**Validado contra tráfego real antes de ativar:** 464.544 linhas do log do `garden`, 171.989 matches. Inspeção manual da amostra do que seria banido: `wp-admin/install.php`, `.git/config`, `.env.local`, `wp-login.php`. Nenhum tráfego legítimo na amostra.

---

## Parte 3 — Pendente

### 3.1 O que apagou a chave em 16 de maio continua por identificar

A versão anterior deste relatório apontava `repair_user.py` ou um re-provisionamento, "pelo padrão". Lido o código, o `repair_user.py` não faz isso: ele cria `~/.ssh` com modo `700` e, quando não há `authorized_keys`, apenas registra o aviso `authorized_keys ausente; não criado porque falta chave pública`. Nunca apaga, nunca sobrescreve. Ver [`repair_user.py`](../scripts/admin/repair_user.py).

Nenhum script de `scripts/admin/` remove esse arquivo. Os únicos que escrevem nele são `create_runv_user.py` e `update_user.py`, e ambos escrevem uma chave.

Portanto a causa está **por identificar**, e há uma hipótese que ninguém testou: o bind mount da jail. O [`runv_jail.py`](../scripts/admin/runv_jail.py) monta a home real em `/srv/jail/<user>`. Se um mount ficar por cima da home no momento em que o sshd lê as chaves, o efeito observado é idêntico ao de um arquivo apagado, e o conserto seria outro. Testar isto antes de auditar qualquer script:

```bash
findmnt -T /home/kirihito
grep -n kirihito /etc/fstab
ls -la /srv/jail/kirihito/.ssh/ 2>/dev/null
grep -c kirihito /var/log/runv-user-provision.log
```

Se voltar a acontecer, apaga a chave de quem for alvo. É a suspeita mais provável para o silêncio de outros membros.

### 3.2 Bloqueio estático de UFW para os dois IPs de scanner

**Não aplicado.** A execução de `ufw insert deny` foi barrada pelo classificador de permissões da sessão. Não foi contornado por `iptables` direto, de propósito.

Deixou de ser necessário: com o fail2ban funcional, o `8.235.68.165` (51.609 requisições) e o `34.150.246.58` (36.449) são banidos automaticamente assim que voltarem, e a jail apanha também os IPs seguintes, que a regra estática não apanharia. Ambos são VMs de cloud descartáveis (Alibaba e Google Cloud) e trocam de IP em um dia.

Se ainda assim quiser as regras estáticas:

```bash
sudo ufw insert 1 deny from 8.235.68.165 comment 'scanner .env'
```

---

## Parte 4 — Como melhorar o runv

### O diagnóstico

O runv não tem problema de audiência. São ~50 visitantes únicos por dia, 167 IPs no Gemini em agosto, e as páginas mais lidas são exatamente as de "como entrar". As pessoas chegam e batem à porta.

O problema é o que acontece depois. Das cinco contas de membro, quatro nunca publicaram, e uma delas estava impedida de entrar desde maio. Com n=5, isso não é estatística; é um sinal com uma causa técnica confirmada em pelo menos um caso.

A pergunta certa, antes de qualquer divulgação: quantos dos outros bateram no mesmo muro?

### Prioridade 1 — Verificar se os outros membros conseguem entrar

Para cada conta: a chave está no lugar, o login funciona, a quota está aplicada, a jail não está quebrada. O `wtmp` mostra que nenhum deles entra desde julho, e depois do caso do `kirihito` "não quis" e "não conseguiu" são indistinguíveis de fora.

Um `scripts/admin/healthcheck_users.py` que valide o estado de cada conta e avise em divergência resolve isto de forma permanente.

### Prioridade 2 — Um segundo fator no cadastro

O caso do `kirihito` expôs que o e-mail é o único âncora de identidade. Com provedores anônimos, quem toma a caixa toma a conta.

O cadastro dele já tinha o antídoto sem que fosse usado: o campo `online_presence`, com `kirihito.envs.net` e `kirihito.oss.zone`, duas contas noutros pubnixes, declaradas em maio.

Para pedidos sensíveis (troca de chave, mudança de e-mail), pedir a publicação de uma frase-desafio numa dessas páginas prova controle de uma identidade independente, estabelecida antes de qualquer comprometimento possível. Custa um e-mail e é bem mais forte do que confiar no DKIM.

### Prioridade 3 — Baixar o atrito do primeiro arquivo

O salto entre "fui aprovado" e "publiquei alguma coisa" é onde todos param. Por ordem de esforço:

- **Um `welcome` interativo no primeiro login** que pergunte três coisas e gere um `index.html` real com as respostas. Sair do primeiro login com uma página no ar que já é sua muda tudo em relação a sair com um placeholder.
- **Um comando `publicar`** que aceite markdown e gere as versões HTML, Gemini e Gopher de uma vez. Hoje o membro precisa entender três formatos e três diretórios para dizer olá.
- **Substituir os placeholders** por algo que não pareça já preenchido. Um `index.html` com conteúdo genérico lê-se como "já está feito"; um arquivo vazio com um comentário dizendo o que fazer convida à edição.

### Prioridade 4 — Dar sinais de vida públicos

Com 50 visitantes por dia lendo `/junte-se/`, a página seguinte devia mostrar uma comunidade viva:

- um índice `/~` com todas as páginas de membros e data da última alteração;
- um feed agregado (`/news/feed.rss` já existe) que junte as atualizações dos membros;
- expor a curva do Gemini em algum lugar: 10 para 167 IPs únicos em cinco meses é o número mais convincente que este projeto tem.

### Prioridade 5 — Higiene

- **Decidir sobre o Nex.** Na semana observada, a porta 1900 só recebeu varredura. Para decidir com base em mais do que uma semana é preciso primeiro dar log persistente ao `nexd`, que hoje escreve só para stderr. Ou se divulga, ou se fecha, ou se instrumenta.
- **Métricas de verdade.** Um GoAccess sobre os logs rotacionados, com filtro de bots, evita arqueologia de `awk` a cada pergunta. Até lá, a seção de metodologia deste relatório é a referência.
- **Rever o `mode = aggressive` do postfix** agora que o fail2ban realmente bane. Durante meses a configuração era teórica; a partir de agora tem efeito real, e vale confirmar que não apanha remetentes legítimos.
- **Vigiar `/var/log/fail2ban.log`.** Estava com 17 MB de erros históricos. Se o arquivo novo voltar a crescer depressa, há outra ação falhando.

---

## Anexo — Arquivos alterados

O repositório tem duas convenções de backup: sufixo com timestamp, `<arquivo>.bak.<AAAAMMDD-HHMMSS>`, usado por [`setup_alt_protocols.py`](../scripts/admin/setup_alt_protocols.py); e diretório dedicado, `/root/runv-fstab-backups/fstab.<AAAAMMDD-HHMMSS>.bak`, usado por [`starthere.py`](../scripts/admin/starthere.py).

Nem `update_user.py` nem `create_runv_user.py` gravam backup. As cópias feitas nesta sessão sobre `users.json` e sobre os vhosts foram manuais, e o caminho de cada uma precisa ficar registrado aqui:

| Arquivo | Ação | Backup |
|---|---|---|
| `/home/kirihito/.ssh/authorized_keys` | criado (chave nova, `600`) | não aplicável (não existia) |
| `/var/lib/runv/users.json` | fingerprint atualizado | `⟨CONFIRMAR: caminho da cópia manual⟩` |
| `/var/www/runv.club/html/data/members.json` | regerado pela ferramenta | não aplicável (derivado) |
| `/etc/apache2/sites-available/garden.runv.club.conf` | regras anti-varredura | `⟨CONFIRMAR: caminho⟩` |
| `/etc/apache2/sites-available/garden.runv.club-le-ssl.conf` | regras anti-varredura | `⟨CONFIRMAR: caminho⟩` |
| `/etc/systemd/journald.conf.d/runv-retention.conf` | criado | não aplicável |
| `/etc/fail2ban/filter.d/runv-webscan.conf` | criado | não aplicável |
| `/etc/fail2ban/jail.d/runv-webscan.conf` | criado | não aplicável |
| pacote `logrotate` | instalado | — |
| pacote `nftables` | instalado | — |

Para localizar as cópias manuais e preencher os três marcadores acima:

```bash
ls -la /var/lib/runv/users.json*
ls -la /etc/apache2/sites-available/garden.runv.club*.conf*
find /root /home/pmurad-admin -maxdepth 3 \
     \( -name 'users.json*' -o -name 'garden.runv.club*conf*' \) 2>/dev/null
```

Se nenhuma cópia aparecer, o marcador passa a `sem backup` — que é informação tão útil quanto o caminho.

**Não alterado:** `snmpd`, a regra UFW `161/udp ALLOW 207.180.232.129`, o `ignoreip` do fail2ban, e tudo o que se relaciona com a monitoração a partir de `207.180.232.129`.

**Serviços verificados no fim:** apache2, fail2ban, systemd-journald, snmpd, dovecot, postfix, molly-brown, runv-nexd — todos `active`. Smoke test com resposta correta em web, Gemini e Gopher.
