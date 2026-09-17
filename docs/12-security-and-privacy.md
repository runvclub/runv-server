# Segurança e privacidade

[← Índice](README.md)

## Factos do código (produto)

- Uso de `subprocess` com **listas de argumentos** — sem `shell=True` nos módulos Python principais verificados em auditorias recentes (`scripts`, `terminal`, `site`, `tools`, `email`, `patches`).
- Fila `entre`: ficheiros criados com **`O_CREAT|O_EXCL`** para evitar sobrescrever pedidos (`entre_core.py`).
- **`members.json` público:** apenas campos acordados em `build_directory.py` — ver [07-public-members-directory.md](07-public-members-directory.md).

## Fila vs site público

- JSONs em `entre-queue/` contêm dados para **revisão admin** (incl. email, chave pública, fingerprint no payload).
- Esses campos **não** devem aparecer no `members.json` servido pelo HTTP — o gerador público não os copia.

## Segredos

- `/etc/runv-email.secrets.json`, chaves SSH privadas, tokens: **nunca** em Git; seguir `.gitignore`.

## Recomendações gerais (não automatizadas pelo repo)

- Firewall, `sshd_config` global, desactivar root login, etc. — política do operador.
- Modo `empty-password` do `entre` é **deliberadamente fraco** para onboarding; docstring de `setup_entre.py` descreve riscos.

## Manutenção

- [relatorio-manutencao-2026-09-17.md](relatorio-manutencao-2026-09-17.md) — auditoria de acessos, fail2ban configurado com `nftables` sem o comando `nft` instalado, `logrotate` ausente, retenção do journald e vhost `garden` a responder `200 OK` a qualquer caminho.

Próximo: [13-troubleshooting.md](13-troubleshooting.md).
