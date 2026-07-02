# gmi2html

## O que é

Biblioteca **Go** que converte documentos **gemtext** (`.gmi`) em **HTML**.

## Para que serve

Permitir que conteúdo escrito no formato Gemini seja exibido em navegadores web. Usada por vários projetos do ecossistema m15o (`ni`, `nightfall-server`, `midnight-pub`).

## O que faz

- Converte headings (`#`, `##`, `###`), links (`=>`), blockquotes, blocos preformatted e listas (`*`)
- Escapa HTML para segurança (`html.EscapeString`)
- API simples: `Convert(gmi string) string`

## Tecnologias

Go 1.15

## Funcionalidades principais

- Suporte completo à sintaxe gemtext
- Sanitização de saída HTML
- Testes em `convert_test.go`

## Repositório

https://git.sr.ht/~m15o/gmi2html
