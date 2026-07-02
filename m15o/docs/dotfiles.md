# dotfiles

## O que é

Coleção de **configurações pessoais** de ambiente desktop Unix/X11 do autor m15o: window manager, sessão X e scripts utilitários.

## Para que serve

Reproduzir o setup de trabalho do autor em máquinas Unix-like — FVWM como window manager, remapeamento de teclas e scripts para conectar/desconectar monitor externo.

## O que faz

- Inicia sessão X com FVWM (`.xsession`, `.fvwmrc`)
- Configura aparência X11 (`.Xdefaults`)
- Fornece scripts `bin/dock` e `bin/undock` para gerenciar monitor externo via xrandr
- Remapeia Caps Lock para Ctrl

## Tecnologias

Shell (ksh), FVWM, X11, xrandr

## Funcionalidades principais

- FVWM com pager, xclock, xload e monitor de bateria
- Scripts de docking/undocking de monitor
- Configuração de teclado e aparência

## Repositório

https://git.sr.ht/~m15o/dotfiles
