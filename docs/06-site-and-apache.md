# Site público e Apache

[← Índice](README.md)

## Conteúdo estático

- **`site/public/`:** HTML, CSS, JS servidos como DocumentRoot após `genlanding.py`.
- **Visual "formulário contínuo":** um único `assets/style.css` (tokens em `:root`, fonte Courier Prime auto-hospedada em `assets/fonts/`). A moldura comum (head, cabeçalho, navegação, rodapé com botões 88x31) vive em **`site/chrome.py`**, usada por `build_home.py`, `wiki/build_wiki.py` e `kiosk.py`. As páginas escritas à mão (`junte-se`, `faq`, `news`, `now` e equivalentes em `en/`) copiam a mesma marcação: ao mudar `chrome.py`, actualize-as.
- **Tom dos textos:** impessoal, directo e técnico. Sem primeira pessoa.

## Home gerada: `site/build_home.py`

A home (`index.html` e `en/index.html`) é gerada, não editada à mão. Fontes:

| Ficheiro | Conteúdo |
|---|---|
| `DocumentRoot/data/members.json` | lista `ls -lt` (já filtrada por `build_directory.py`; o script não lê `users.json`) |
| `--homes-root /home` | data do `public_html/index.html` e contagem de ficheiros |
| `/etc/os-release`, `/proc/meminfo`, disco | linha `uname`/status |
| `site/home.pt.txt`, `site/home.en.txt` | texto do `cat /etc/motd` |
| `site/diario.txt` | changelog (`AAAA-MM-DD \| pt \| en`, 8 mais recentes) |

- **`genlanding.py`** (completo e `--sync-public-only`) corre `build_home.py` **depois** de copiar `site/public/` e regenerar `members.json`, porque a cópia apaga o DocumentRoot. `--no-build-home` desliga.
- **`--members-homes-root`** passa a `/home` por omissão quando a pasta existe.
- **Timer horário:** `site/systemd/runv-home.{service,timer}` regenera `members.json` e a home sem recopiar o resto. Instalação no cabeçalho do `.service` (ajustar `RUNV_REPO` se o checkout não estiver em `/opt/runv-server`):

```bash
sudo install -m 644 site/systemd/runv-home.service site/systemd/runv-home.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now runv-home.timer
sudo systemctl start runv-home.service && journalctl -u runv-home.service -n 20
```

- A `site/public/index.html` versionada é só o fallback (gerada localmente com `--facts-json`).

## Script: `site/genlanding.py`

- Configura VirtualHost Apache, `mod_userdir`, `mod_rewrite`, copia `site/public` → DocumentRoot.
- Modo produção: domínio predefinido `runv.club`, DocumentRoot predefinido `/var/www/runv.club/html`.
- Modo `--dev`: `runv.local`, `/var/www/runv-dev/html`.
- Opcional: `--certbot` (incompatível com `--dev`).
- Após cópia, por omissão chama `build_directory.py` para gravar `data/members.json` no DocumentRoot (`--no-refresh-members` para omitir).
- **`--sync-public-only`:** só copia `site/public/` → DocumentRoot, `chown www-data` e regenera `members.json`; **não** altera Apache (uso típico após `create_runv_user.py` e disponível para correr à mão).
- **RSS (`/news/feed.rss`):** o `genlanding` completo (sem `--sync-public-only`) grava `/etc/apache2/conf-available/runv-landing-rss-mime.conf` com **`RemoveType`**, **`ForceType text/xml`** e **`Header set Content-Type`** (sobrepor `mod_mime` / `application/rss+xml`), activa **`a2enmod headers`** e **`a2enconf runv-landing-rss-mime`**. O snippet é **global** ao Apache (**:80 e :443**) sem editar o VirtualHost SSL do Certbot. Após mudar o DocumentRoot, volte a correr o `genlanding` completo para actualizar o snippet.
- Versão actual do script: constante `VERSION` no ficheiro (ex.: `0.07`).

## TLS e DNS

- **Recomendação:** DNS a apontar para o servidor antes de Certbot (documentado historicamente).

## Lista de membros na home

- A constelação (`app.js`) foi removida; a lista `ls -lt` da home ocupa o lugar dela.
- Após **`create_runv_user.py`:** se `--landing-document-root` existir como directório, o script corre **`genlanding.py --sync-public-only`** (cópia de `site/public/` + `members.json` + home) e imprime **`landing (public + bolhas)`** ou **AVISO** se faltar path ou falhar (**evidência:** `create_runv_user.py`).

Próximo: [07-public-members-directory.md](07-public-members-directory.md).
