# bitters

## O que é

Editor de texto inspirado no **Canon Cat** (Jef Raskin), focado em processamento de palavras com paradigmas alternativos de navegação e edição.

## Para que serve

Explorar interfaces de edição que fogem do modelo tradicional de cursor + teclas de seta. O bitters implementa o conceito de "leap" (salto por teclas modificadoras) e modos de composição inspirados em máquinas de escrever inteligentes.

## O que faz

- Abre e edita documentos em modos distintos (compose, leap, highlight, command)
- Navega por texto com saltos contextuais (Alt + tecla)
- Gerencia buffers e disco via abstrações próprias (`disk.c`, `buffer.c`)
- Inclui manual embutido (`manual.bit`)

## Tecnologias

C, SDL2

## Funcionalidades principais

- Modos de edição: compose, leap (frente/trás), highlight, command
- Navegação "leap" por teclas modificadoras
- Configuração em `config.h`
- Build via `build.sh`

## Repositório

https://git.sr.ht/~m15o/bitters
