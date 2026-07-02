# tny

## O que é

**Máquina virtual minimalista** (VM de 256 bytes de RAM) com emulador gráfico e assembler próprio — projeto experimental de baixo nível.

## Para que serve

Explorar computação de baixo nível: uma ISA própria, display de 32 pixels, pilhas e I/O por teclado — educação e experimentação com sistemas tiny.

## O que faz

- Emula VM com ~40 mnemonics (pilhas, jumps, aritmética, I/O)
- Display de 32 pixels via SDL2
- Loop de 60 FPS com controle por teclado (setas + X/C)
- Assembler de texto para ROM binária (`.rom`)
- Dump de estado ao encerrar (pilhas, RAM, buffer, tela)

## Tecnologias

C (C89), SDL2

## Funcionalidades principais

- Emulador: `src/tnyemu.c`
- Assembler: `src/tnyasm.c`
- Build via `build.sh`

## Repositório

https://hg.sr.ht/~m15o/tny
