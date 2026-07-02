# owl-report

## O que é

**Leitor de feeds de internet** (RSS/Atom) auto-hospedável, com visão agregada "report" de todas as assinaturas.

## Para que serve

Substituir leitores de feed centralizados por uma instância própria: cadastrar feeds, categorizar, importar OPML e ver um relatório HTML agregado por data.

## O que faz

- Cadastro, login e painel admin
- Gestão de feeds e categorias
- Importação/exportação OPML
- Fetch concorrente de feeds (até 10 paralelos)
- Visão "report" agregada por data de publicação
- CSS personalizável por usuário
- Gera relatório HTML estático (`report/tpl.html`)

## Tecnologias

Go 1.18, Gorilla (mux/sessions/CSRF), PostgreSQL, `feed`, `opml`

## Funcionalidades principais

- Leitor RSS/Atom self-hosted
- Import/export OPML
- Report HTML agregado

## Repositório

https://git.sr.ht/~m15o/owl-report
