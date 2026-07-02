# html-journal

## O que é

Servidor web análogo ao `html-blog`, mas para o formato **HTML Journal** — diários e atualizações pessoais em HTML puro.

## Para que serve

Definir e validar um padrão de journal na web: página com `<h1>` e `<article>` contendo `<h2>` (data) e conteúdo. Site de referência: [journal.miso.town](https://journal.miso.town).

## O que faz

- Valida documentos HTML Journal
- Converte journals válidos em feed Atom
- Integra com o agregador **The Neon Kiosk**
- Usa a biblioteca `htmlj` para parsing

## Tecnologias

Go 1.18, templates HTML embutidos

## Funcionalidades principais

- `/validate-by-url` e `/validate-by-input`
- `/journal-to-atom` — conversão para Atom
- Formato: `<h1>` + `<article>` com `<h2>` e conteúdo

## Repositório

https://git.sr.ht/~m15o/html-journal
