# html-blog

## O que é

Servidor web que define e promove o formato **HTML Blog** — blogs escritos em HTML puro, com validação online e conversão para feed Atom.

## Para que serve

Estabelecer um padrão simples de blog na web sem frameworks: uma página HTML com `<h1>`, lista de `<time>` e `<a href>`. O site de referência é [blog.miso.town](https://blog.miso.town).

## O que faz

- Valida páginas HTML Blog por URL ou por input direto
- Converte blogs válidos em feed Atom
- Documenta o formato na página inicial
- Usa a biblioteca `htmlb` para parsing

## Tecnologias

Go 1.18, templates HTML embutidos

## Funcionalidades principais

- `/validate-by-url` e `/validate-by-input`
- `/blog-to-atom` — conversão para Atom
- Formato: `<h1>` + `<time>` + `<a href>` por entrada

## Repositório

https://git.sr.ht/~m15o/html-blog
