# yon

## O que é

**Wiki/editor de notas** auto-contido num único arquivo HTML — app client-side para escrita com links `[[página]]`, sem backend.

## Para que serve

Organizar conhecimento pessoal no navegador com wiki local, busca full-text e export — similar ao `moka`, mas com foco em UI para conhecimento e comandos avançados.

## O que faz

- Múltiplos painéis editáveis lado a lado com redimensionamento
- Armazenamento em `localStorage` com histórico back/forward por painel
- Links wiki `[[nome]]`, busca full-text, referências (`+ref`, `+orph`, `+ls`)
- Comandos: log diário, renomear (`mv`), deletar, reset total
- Export JSON, import de arquivo, **save como HTML** (quine — o app se reescreve com dados embutidos)

## Tecnologias

HTML, CSS, JavaScript vanilla — arquivo único `yon.html`

## Funcionalidades principais

- Wiki local multi-painel
- Busca e backlinks
- Export quine (HTML autocontido)

## Repositório

https://git.sr.ht/~m15o/yon
