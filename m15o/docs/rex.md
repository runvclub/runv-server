# rex

## O que é

**Navegador mínimo de linha de comando** para o protocolo **Nex**, usando `netcat` e `less`.

## Para que serve

Navegar em estações Nex a partir do terminal, com implementação extremamente leve (~10 linhas de shell) — ideal para ambientes Unix minimalistas.

## O que faz

- Conecta via TCP na porta 1900
- Envia o seletor (caminho) e exibe resposta via `less`
- Uso: `rex [host] [selector]`

## Tecnologias

ksh (shell script)

## Funcionalidades principais

- Cliente Nex de terminal
- Implementação mínima
- Sem dependências além de netcat e less

## Repositório

https://hg.sr.ht/~m15o/rex
