# nexd

## O que é

Daemon **TCP** que implementa o protocolo **Nex** nativo na porta **1900** — o "Nightfall Express".

## Para que serve

Servir conteúdo estático no protocolo Nex da small web, permitindo que clientes como `nova`, `rex` e `warp` naveguem em estações Nex.

## O que faz

- Escuta na porta `:1900`
- Recebe uma linha de seleção por cliente e responde com conteúdo Nex
- Serve arquivos de um diretório raiz (`nexd /var/nex`)
- Uma goroutine por conexão

## Tecnologias

Go (usa `nex-pfm`)

## Funcionalidades principais

- Servidor Nex nativo
- Concorrência por conexão
- Instalação como daemon OpenBSD documentada no README

## Repositório

https://hg.sr.ht/~m15o/nexd
