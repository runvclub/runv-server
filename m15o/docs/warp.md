# warp

## O que é

**Navegador web minimalista** para o protocolo **Nex** (rede Nightfall City), traduzindo conteúdo Nex para HTML no browser.

## Para que serve

Navegar em estações Nex usando apenas um navegador web — sem instalar cliente dedicado. Alternativa web ao `nova` (GUI) e `rex` (terminal).

## O que faz

- Conexão TCP na porta 1900 para hosts `nex://`
- Barra de URL e navegação "up" em diretórios
- Renderiza links `=>` como hyperlinks HTML
- Suporte a imagens JPEG inline
- Resolve caminhos relativos no protocolo Nex

## Tecnologias

PHP (arquivo único `warp.php`)

## Funcionalidades principais

- Cliente Nex via browser
- Renderização Nex → HTML
- Navegação por diretórios

## Repositório

https://hg.sr.ht/~m15o/warp
