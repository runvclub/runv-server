# the-neon-kiosk

## O que é

**Agregador estático** que monta um "quiosque virtual" reunindo entradas recentes de [HTML Journals](https://journal.miso.town) e [HTML Blogs](https://blog.miso.town) de sites externos. Site público: [kiosk.nightfall.city](https://kiosk.nightfall.city).

## Para que serve

Descobrir conteúdo recente da small web num único lugar — um feed curado de journals e blogs HTML sem precisar visitar cada site individualmente.

## O que faz

- Lê listas de URLs de arquivos de entrada (journals e blogs)
- Busca remota, filtra posts do último mês, ordena por data
- Resolve links/imagens relativos para URLs absolutas
- Gera páginas HTML estáticas (`tpl.html`, `tpl-blog.html`)
- Página de submissão (`join.html`) para novos sites

## Tecnologias

Go 1.18, bibliotecas `htmlj` e `htmlb`, templates HTML embutidos

## Funcionalidades principais

- Agregação de HTML Journals e Blogs
- Geração estática de HTML
- Filtro por recência (último mês)

## Repositório

https://git.sr.ht/~m15o/the-neon-kiosk
