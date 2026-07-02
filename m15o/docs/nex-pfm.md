# nex-pfm

## O que é

Biblioteca **Go** que implementa o protocolo **Nex** para servir arquivos e listar diretórios — a camada de plataforma (PFM = platform) do ecossistema Nex.

## Para que serve

Ser a biblioteca central usada por `nexd` (servidor TCP nativo) e `kinex` (gateway HTTP) para servir conteúdo no protocolo Nex da Nightfall City.

## O que faz

- Lista diretórios com links `=>`
- Suporta arquivos `.header` para cabeçalhos customizados
- Ordena por nome (`.desc`) ou data de modificação (`.modified`)
- Serve arquivo `index` dentro de pastas

## Tecnologias

Go (biblioteca, não binário standalone)

## Funcionalidades principais

- Handler `Handle(path, io.Writer)` para requisições Nex
- Listagem e serving de arquivos
- Dependência compartilhada de `nexd` e `kinex`

## Repositório

https://hg.sr.ht/~m15o/nex-pfm
