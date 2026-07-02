#!/bin/sh -e

cc -g -std=c89 -Wall -pedantic -o bin/tnyemu src/tnyemu.c $(sdl2-config --cflags --libs)
cc -g -std=c89 -Wall -pedantic -o bin/tnyasm src/tnyasm.c

