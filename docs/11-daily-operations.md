# Operação diária (dia 2+)

[← Índice](README.md)

## Adicionar membro

1. Pedido via `entre` ou processo interno.
2. `sudo python3 scripts/admin/create_runv_user.py …` (ver `--help` no servidor).
3. Confirmar linha **`landing (public + bolhas): sincronizado`** ou corrigir com `genlanding.py --sync-public-only` (ou só `build_directory.py` se bastar actualizar `members.json`).

## Actualizar lista pública sem novo membro

Só regenerar **`members.json`**:

```bash
sudo python3 REPO/site/build_directory.py \
  --users-json /var/lib/runv/users.json \
  -o /var/www/runv.club/html/data/members.json
```

Recopiar também **`site/public/`** (assets/HTML) para o DocumentRoot + `members.json`:

```bash
sudo python3 REPO/site/genlanding.py --sync-public-only \
  --document-root /var/www/runv.club/html \
  --members-users-json /var/lib/runv/users.json
```

(Ajustar paths ao teu DocumentRoot.)

## Após `git pull` no servidor

- `sudo python3 tools/tools.py` para MOTD/skel/bin conforme alterações.

## Notícias

- Colocar `.md` em `site/news/`, executar **`sudo python3 REPO/site/news/publish_news.py`** em produção. O script grava `site/public/news/` (JSON, RSS, sitemap) e, se **`/var/www/runv.club/html`** existir, invoca **`site/genlanding.py --sync-public-only`** no fim (copia `site/public/` para o DocumentRoot + `data/members.json`). Se o DocumentRoot não existir no ambiente (ex.: só clone local), aparece um AVISO com o comando manual — a publicação em `site/public/` fica feita.
- **`--skip-genlanding`:** só gera ficheiros em `site/public/` sem copiar para Apache.
- Ajustar paths com `--landing-document-root`, `--members-users-json` e opcionalmente `--members-homes-root` se a tua instalação divergir dos defaults.

## Wiki

- Fontes em `site/wiki/` (pt) e `site/wiki/en/` (en). Primeira linha = título; linhas `## ` = subtítulos, em sentença normal (sem caixa alta).
- Regenerar sempre as duas línguas, senão o sitemap perde as URLs da outra: `sudo python3 REPO/site/wiki/build_wiki.py --locale all`.

## Home: changelog, motd e /now

- **Changelog:** acrescentar uma linha em `site/diario.txt` (`AAAA-MM-DD | pt | en`). A home mostra as 8 mais recentes.
- **Texto do motd:** `site/home.pt.txt` e `site/home.en.txt`.
- **/now:** editar `site/public/now/index.html` e `site/public/en/now/index.html` (actualizar a data).
- Publicar: `git pull` no servidor e `sudo python3 REPO/site/genlanding.py --sync-public-only` (ou esperar o timer `runv-home`, que só refaz a home e o `members.json`).
- Tom: impessoal, directo, técnico.

## Email

- Testes documentados no módulo `email/` (`send_test_mail.sh`, etc., se presentes).

Próximo: [12-security-and-privacy.md](12-security-and-privacy.md).
