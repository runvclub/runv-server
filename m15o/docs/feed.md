# feed

## O que é

Biblioteca **Go** para parsear feeds web **RSS** e **Atom** em uma estrutura unificada.

## Para que serve

Servir como dependência para aplicações que consomem feeds de notícias e blogs — como o `owl-report` — sem precisar lidar separadamente com os formatos RSS e Atom.

## O que faz

- Recebe bytes de um feed e detecta automaticamente o formato (RSS ou Atom)
- Extrai título, URL e data de publicação de cada entrada
- Retorna entradas ordenadas por data

## Tecnologias

Go 1.18

## Funcionalidades principais

- Detecção automática de formato (`format.go`)
- Parsers separados: `rss.go`, `atom.go`
- Tipos `Feed` e `Entry` unificados
- API principal: `Parse(data []byte)`

## Repositório

https://git.sr.ht/~m15o/feed
