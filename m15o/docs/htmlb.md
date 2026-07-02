# htmlb

## O que é

Biblioteca **Go** que faz parse de páginas no formato **HTML Blog**, extraindo título e entradas com data e link.

## Para que serve

Ser a camada de parsing usada pelo `html-blog` e pelo `the-neon-kiosk` para validar blogs e gerar feeds Atom a partir de HTML puro.

## O que faz

- Percorre o DOM HTML buscando `<h1>`, `<time>` e `<a>`
- Retorna estrutura `Blog` com slice de `Entry` (título, href, data)
- Valida datas no formato esperado

## Tecnologias

Go 1.18, `golang.org/x/net/html`

## Funcionalidades principais

- Tipos `Blog` e `Entry`
- API: `Parse(r io.Reader) (*Blog, error)`
- Testes em `htmlb_test.go`

## Repositório

https://git.sr.ht/~m15o/htmlb
