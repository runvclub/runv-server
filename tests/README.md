# Testes — runv-server

Testes de unidade em `unittest` (só biblioteca padrão, fiel ao resto do projeto).
Cobrem as zonas de maior consequência: a política de validação que corre como root
e as garantias de segurança do conteúdo público.

## Correr

Exigem ambiente **Unix** (os módulos importam `pwd`/`fcntl` e usam `os.geteuid`).
Em Linux, no servidor, ou em WSL:

```bash
cd <raiz-do-repo>
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

Em plataformas sem esses módulos (ex.: Windows nativo) os testes são **ignorados**
automaticamente em vez de falhar. Para só verificar sintaxe em qualquer SO:

```bash
python3 -m compileall -q scripts terminal site tools email patches tests
```

## O que cobrem

- **`test_validation_parity.py`** — trava a duplicação intencional das constantes de
  política (`USERNAME_PATTERN`, `EMAIL_PATTERN`, `ALLOWED_KEY_TYPES`,
  `RESERVED_USERNAMES`, `MAX_EMAIL_LEN`) entre `terminal/entre_core.py`,
  `create_runv_user.py`, `update_user.py`, `del-user.py` e `build_directory.py`.
  Estes módulos mantêm cópias próprias por desenho (não se importam em runtime); o
  teste garante que não há *drift* silencioso. **Ao alterar uma dessas constantes
  num módulo, altere em todos** — é o que este teste exige.
- **`test_provisioning_validation.py`** — comportamento de `validate_username`,
  `validate_email` e `normalize_public_key` do provisionador (caminho root).
- **`test_news_rendering.py`** — regressão de XSS: o gerador de notícias escapa todo
  o conteúdo e rejeita `javascript:`/`data:` em hrefs (o cliente usa `innerHTML`).
- **`test_members_directory.py`** — o diretório público só expõe `username`/`since`/
  `path` (nunca email, fingerprint ou quota) e descarta usernames inválidos.
