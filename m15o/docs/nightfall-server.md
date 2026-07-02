# nightfall-server

## O que é

Servidor de produção para **[nightfall.city](https://nightfall.city)**, combinando hospedagem **Gemini** e proxy **HTTP** que converte conteúdo Gemini para HTML.

## Para que serve

Hospedar o conteúdo da Nightfall City em múltiplos protocolos: Gemini nativo e HTTP para navegadores web.

## O que faz

- Serve arquivos estáticos Gemini em `gmi/`
- Rota HTTP `/gemini/` com conversão `gmi2html`
- Serve HTML estático adicional
- HTTPS automático em produção (Let's Encrypt / autocert)
- CSS embutido com suporte a dark mode

## Tecnologias

Go 1.16 (`go-gemini`, ACME/Let's Encrypt)

## Funcionalidades principais

- Servidor Gemini + gateway HTTP
- TLS automático
- Dark mode no CSS

## Repositório

https://git.sr.ht/~m15o/nightfall-server
