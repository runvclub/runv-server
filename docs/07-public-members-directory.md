# Directório público de membros

[← Índice](README.md)

## Script: `site/build_directory.py`

- **Entrada:** `--users-json` (default `/var/lib/runv/users.json`) — deve ser uma **lista** JSON de objectos.
- **Saída:** `-o` / `--output` (default no repo: `site/public/data/members.json`; em produção típico: `DocumentRoot/data/members.json`).

## Schema público (campos escritos)

Cada elemento do array gerado contém:

| Campo | Origem / notas |
|-------|------------------|
| `username` | De `users.json` |
| `since` | `created_at` se for string; senão `""` |
| `path` | `"/~username/"` |
| `homepage_mtime` | Só com `--homes-root`. `genlanding.py` e o timer `runv-home` passam `/home` por omissão |

**Privacidade:** o script **não** copia email, fingerprint SSH, quotas nem outros campos internos (**evidência:** lógica em `build_directory.py`, função `main`).

## Consumo no browser

- `site/build_home.py` lê o `members.json` para a lista `ls -lt` da home (descarta usernames fora da política; ver `tests/test_build_home.py`).
- `site/public/assets/home.js` usa `path` para o botão "página aleatória".

## Quando regenerar

1. **Hook em `create_runv_user.py`:** se `--landing-document-root` existir como directório e **não** usar `--no-refresh-landing-members`, o script invoca `site/genlanding.py --sync-public-only` — copia `site/public/` para o DocumentRoot, `chown www-data` e corre `build_directory.py` para `data/members.json` (equivalente a sincronizar landing + bolhas num único passo).
2. **`genlanding.py` completo** (primeira instalação / Apache): após `copy_landing`, por omissão também regenera `members.json` (a menos de `--no-refresh-members`).
3. **Timer `runv-home` (de hora em hora):** regenera `members.json` e a home. Ver [06-site-and-apache.md](06-site-and-apache.md).
4. **Manual — só `members.json` (sem recopiar `public/`):**

```bash
python3 REPO/site/build_directory.py \
  --users-json /var/lib/runv/users.json \
  -o /var/www/runv.club/html/data/members.json
```

5. **Manual — `public/` + `members.json` (sem reconfigurar Apache):**

```bash
sudo python3 REPO/site/genlanding.py --sync-public-only \
  --document-root /var/www/runv.club/html \
  --members-users-json /var/lib/runv/users.json
```

## Cron vs hooks (sem contradição)

- **Hooks** actualizam quando corres `create_runv_user` (sync-only) ou `genlanding` (completo ou sync-only).
- **Cron** com `build_directory.py` é **opcional** para alinhar só o JSON sem tocar no resto do DocumentRoot.

Próximo: [08-email.md](08-email.md).
