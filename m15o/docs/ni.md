# ni

## O que é

Gerador de **wiki estática** a partir de arquivos **Gemini** (`.gmi`), com links entre páginas e backlinks automáticos.

## Para que serve

Publicar wikis estáticos a partir de gemtext, sem banco de dados ou servidor dinâmico — ideal para a small web.

## O que faz

- Processa arquivos `.gmi` com sintaxe `[[pagina]]` para links wiki
- Converte Gemini → HTML via `gmi2html`
- Gera backlinks automaticamente
- Produz página de changelog e feed Atom a partir de templates XML

## Tecnologias

Go 1.16

## Funcionalidades principais

- Wiki estática com backlinks
- Feed Atom
- Conversão gemtext → HTML

## Repositório

https://git.sr.ht/~m15o/ni
