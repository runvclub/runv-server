# riku

## O que é

Serviço para **coletar e gerenciar respostas** enviadas por formulários HTML — backend de formulários de contato/feedback com painel para o dono da conta.

## Para que serve

Substituir serviços como Formspree ou Google Forms por uma instância própria: receber submissões de formulários HTML estáticos e visualizá-las num inbox.

## O que faz

- Endpoint público `/submit` para receber formulários
- Inbox/arquivo de respostas, visualização individual, exclusão
- Registro/login com chave de convite (`KEY`)
- Feed Atom (`/feed.atom`)
- Página de agradecimento e manual embutido

## Tecnologias

Go 1.16, PostgreSQL, Gorilla Mux/Sessions

## Funcionalidades principais

- Backend de formulários HTML
- Inbox com feed Atom
- Registro com convite

## Repositório

https://git.sr.ht/~m15o/riku
