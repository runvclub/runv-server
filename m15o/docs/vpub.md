# vpub

## O que é

Software de **fórum/message board** simples e auto-hospedável, com hierarquia fórum → board → tópico → post.

## Para que serve

Hospedar discussões estruturadas em fóruns e boards, com feeds Atom e painel admin — alternativa leve a plataformas como Discourse.

## O que faz

- Fóruns, boards, tópicos e posts com paginação
- Registro, login, reset de senha, perfil de conta
- Painel admin (usuários, fóruns, boards, chaves API)
- Feeds Atom por board/tópico
- Cria admin padrão (`admin/admin`) na primeira execução
- Conversão de sintaxe de markup em posts

## Tecnologias

Go 1.16, PostgreSQL, Gorilla CSRF/Mux/Sessions

## Funcionalidades principais

- Fórum hierárquico completo
- Feeds Atom
- Admin e API keys

## Repositório

https://git.sr.ht/~m15o/vpub
