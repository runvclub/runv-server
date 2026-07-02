# grid

## O que é

Editor de texto inspirado no **ACME**, implementado em **Gridscript** (linguagem estilo Forth) com engine nativa em C.

## Para que serve

Explorar interfaces de edição minimalistas no estilo Plan 9/ACME, com uma linguagem de script própria para estender o comportamento do editor.

## O que faz

- Executa scripts Gridscript (`.gs`) via interpretador `gs`
- Fornece FFI com `libgrid` para desenho, scroll, buffers, load/save, find e paste
- Inclui biblioteca padrão em `std.gs`
- Ponto de entrada principal: `grid.gs`

## Tecnologias

C, CMake, SDL2, Gridscript (`.gs`)

## Funcionalidades principais

- Editor multi-buffer com scroll e busca
- Linguagem Gridscript para automação
- Build com CMake (Unix e macOS)

## Repositório

https://git.sr.ht/~m15o/grid
