# ichi

## O que é

**Ichi** é uma pequena comunidade online onde pessoas criam **homepages gratuitas**, listadas num índice central para descoberta e interação. O serviço público roda em [ichi.city](https://ichi.city).

## Para que serve

Oferecer hospedagem simples de páginas pessoais na "small web", com subdomínio por usuário, editor web e upload de arquivos — sem a complexidade de um CMS tradicional.

## O que faz

- Registro e login com sessões
- Cria subdomínios por usuário (`user.ichi.city`)
- Editor web, upload e gestão de arquivos/pastas
- SFTP chroot com quota de disco por usuário
- Índice público de homepages e perfis
- Watcher (`inotify`) para sincronizar arquivos com o banco

## Tecnologias

Go, PostgreSQL, SFTP (chroot), Gorilla (sessões)

## Funcionalidades principais

- Hospedagem multi-usuário com quota
- Interface web + SFTP para gerenciar arquivos
- Índice comunitário de homepages

## Repositório

https://git.sr.ht/~m15o/ichi
