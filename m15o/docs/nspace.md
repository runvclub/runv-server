# nspace

## O que é

**Linguagem de programação** e interpretador para **máquinas de registradores** (register machines).

## Para que serve

Experimentação e ensino de programação em um modelo computacional minimalista — duas memórias de dados, acumuladores e conjunto de instruções próprio.

## O que faz

- Executa programas a partir de arquivo fonte
- Manipula DM1/DM2 (memórias de dados) e acumuladores
- Suporta labels e controle de fluxo (`(`, `)`, `{`, `}`, `|`, `;`)
- Compila com `cc nspace.c -o nspace`

## Tecnologias

C

## Funcionalidades principais

- ISA própria (incremento, cópia, saltos, loops)
- Duas memórias e acumuladores
- Documentação em [moka.pub/m15o#nspace](https://moka.pub/m15o#nspace)

## Repositório

https://git.sr.ht/~m15o/nspace
