# nini

## O que é

Gerador de **wiki estática** semelhante ao `ni`, mas usando arquivos **HTML** (`.htm`) como fonte, com backlinks automáticos. O nome sugere ser "a nova ni".

## Para que serve

Publicar wikis estáticos a partir de HTML simples, sem gemtext — alternativa ao `ni` para quem prefere escrever em HTML.

## O que faz

- Lê arquivos `.htm` e gera HTML renderizado
- Calcula backlinks a partir de links internos
- Usa templates Go com `{{ .Title }}`, `{{ .Content }}`, `{{ .Backlinks }}`
- Gera índice e páginas individuais

## Tecnologias

Go 1.18

## Funcionalidades principais

- Wiki estática baseada em HTML
- Backlinks automáticos
- Templates Go

## Repositório

https://git.sr.ht/~m15o/nini
