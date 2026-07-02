# status

## O que é

Serviço de **microblogging de status curtos** no estilo [status.cafe](https://status.cafe) — usuários publicam atualizações rápidas com emoji e texto.

## Para que serve

Compartilhar pensamentos breves e presença online sem a complexidade de redes sociais tradicionais — micro-updates com menções e feeds.

## O que faz

- CRUD de status com menções `@usuario` e links automáticos
- Perfis públicos, feeds Atom por usuário (`/users/{user}.atom`)
- API JSON (`/users/{user}/status.json`) e widget embeddable
- Badges PNG com emoji (`/users/{user}/badge.png`)
- Integração com **vpub** para chaves de fórum
- Registro manual opcional, painel admin

## Tecnologias

Go 1.16, PostgreSQL, Gorilla (CSRF, Mux, Sessions)

## Funcionalidades principais

- Microblogging de status curtos
- Feeds Atom e API JSON
- Widget e badges embeddable

## Repositório

https://git.sr.ht/~m15o/status
