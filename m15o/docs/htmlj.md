# htmlj

## O que é

Biblioteca **Go** que faz parse de documentos no formato **HTML Journal**, extraindo título, entradas e datas de publicação.

## Para que serve

Ser a camada de parsing usada pelo `html-journal` e pelo `the-neon-kiosk` para validar journals e gerar feeds a partir de HTML puro.

## O que faz

- Percorre HTML buscando `<h1>`, `<article>`, `<h2>` (data) e conteúdo
- Retorna estrutura `Journal` com slice de `Entry`
- Valida datas no formato `YYYY-MM-DD`

## Tecnologias

Go 1.18

## Funcionalidades principais

- Tipos `Journal` e `Entry`
- API: `Parse(io.Reader) (*Journal, error)`
- Testes em `htmlj_test.go`

## Repositório

https://git.sr.ht/~m15o/htmlj
