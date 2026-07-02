# nexy

## O que é

Servidor **proxy** que expõe conteúdo do protocolo **Nex** via **Gemini**, permitindo usar clientes Gemini (ex.: Amfora) para navegar em espaços Nex.

## Para que serve

Fazer ponte entre dois protocolos da small web: quem tem cliente Gemini pode acessar conteúdo Nex sem instalar um cliente Nex dedicado.

## O que faz

- Servidor TLS na porta 1965 (Gemini)
- Busca recursos `nex://` via TCP na porta 1900
- Detecta MIME com `file-type`
- Gera certificados com `npm run gencert`

## Tecnologias

JavaScript / Node.js (ES modules)

## Funcionalidades principais

- Proxy Nex → Gemini
- Integração documentada com Amfora
- TLS e detecção de tipo de arquivo

## Repositório

https://hg.sr.ht/~m15o/nexy
