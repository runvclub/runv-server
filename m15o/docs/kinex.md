# kinex

## O que é

Servidor **HTTP** que expõe uma estação **Nex** na web, convertendo conteúdo Nex/gemtext para HTML.

## Para que serve

Permitir que conteúdo hospedado no protocolo Nex seja acessível via navegador web comum, sem precisar de um cliente Nex dedicado.

## O que faz

- Serve arquivos de um diretório raiz Nex
- Converte Nex → HTML (títulos, listas, links, preformatted)
- Suporta templates CSS personalizáveis (`-t`, `-s`)
- Gera breadcrumbs de navegação

## Tecnologias

Go (usa `nex-pfm`)

## Funcionalidades principais

- Gateway HTTP para protocolo Nex
- Templates e estilos customizáveis
- Navegação com breadcrumbs

## Repositório

https://hg.sr.ht/~m15o/kinex
