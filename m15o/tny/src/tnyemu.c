#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <SDL.h>

#define LEN 256
#define FRAME_DURATION (1000 / 60)
#define PIX_WIDTH 10

typedef struct Stack {
	Uint8 dat[LEN];
	int top;
} Stack;

typedef struct Tny {
	Uint8 ram[LEN];
	Stack ps, rs;
} Tny;

Uint8 scn[32];
Uint8 buffer[LEN];
Uint8 controller;
Uint8 frame;

SDL_Window *window;
SDL_Renderer *renderer;

int halt(Tny *t, Uint8 op, Uint8 ip, Uint8 err)
{
	printf("ERROR %d at %d (0x%02x)\n", err, ip, op);
	return 0;
}

/* clang-format off */

#define HALT(c)	{ return halt(t, op, ip - 1, (c)); }
#define PUSH(s, v) {if ((s)->top == LEN) HALT(1)	(s)->dat[(s)->top++] = (v);	}
#define POP(s, v) {	if ((s)->top == 0) HALT(2) *(v) = (s)->dat[--(s)->top]; }
#define POPr1 POP(ps, &r1)
#define POPr2 POP(ps, &r2)

/* eval starting at ip; return 1 on success 0 otherwise */
int eval(Tny *t, Uint8 ip)
{
	Uint8 op, r1, r2, r3;
	Stack *ps = &t->ps;
	for (;;) {
		op = t->ram[ip++];
		switch (op) {
		case 0x00: /* BRK */ return 1; break;
		case 0x01: /* RET */ POP(&t->rs, &ip) break;
		case 0x02: /* JMP */ POP(ps, &ip) break;
		case 0x03: /* JMR */ PUSH(&t->rs, ip) POP(ps, &ip) break;
		case 0x04: /* JCN */ POPr1 POPr2 ip = r2? r1 : ip; break;
		case 0x05: /* JCR */ POPr1 POPr2 if (r2) {	PUSH(&t->rs, ip);	ip = r1; } break;
		case 0x06: /* LIT */ PUSH(ps, t->ram[ip++]) break;
		case 0x07: /* POP */ POPr1 break;
		case 0x08: /* DUP */ POPr1 PUSH(ps, r1) PUSH(ps, r1); break;
		case 0x09: /* SWP */ POPr1 POPr2 PUSH(ps, r1) PUSH(ps, r2) break;
		case 0x0a: /* ROT */ POPr1 POPr2 POP(ps, &r3) PUSH(ps, r2) PUSH(ps, r1) PUSH(ps, r3) break;
		case 0x0b: /* OVR */ POPr1 POPr2 PUSH(ps, r2) PUSH(ps, r1) PUSH(ps, r2) break;
		case 0x0c: /* PSH */ POPr1 PUSH(&t->rs, r1) break;
		case 0x0d: /* PUL */ POP(&t->rs, &r1) PUSH(ps, r1) break;
		case 0x0e: /* RSI */ POP(&t->rs, &r1) PUSH(&t->rs, r1) PUSH(ps, r1) break;
		case 0x0f: /* RSJ */ POP(&t->rs, &r1) POP(&t->rs, &r2) PUSH(&t->rs, r2) PUSH(&t->rs, r1) PUSH(ps, r2) break;
		case 0x10: /* STA */ POPr1 POPr2 t->ram[r1] = r2; break;
		case 0x11: /* LDA */ POPr1 PUSH(ps, t->ram[r1]) break;
		case 0x12: /* STB */ POPr1 POPr2 buffer[r1] = r2; break;
		case 0x13: /* LDB */ POPr1 PUSH(ps, buffer[r1]) break;
		case 0x14: /* ADD */ POPr1 POPr2 PUSH(ps, r1 + r2) break;
		case 0x15: /* SUB */ POPr1 POPr2 PUSH(ps, r2 - r1) break;
		case 0x16: /* INC */ POPr1 PUSH(ps, r1 + 1) break;
		case 0x17: /* DEC */ POPr1 PUSH(ps, r1 - 1) break;
		case 0x18: /* MUL */ POPr1 POPr2 PUSH(ps, r2 * r1) break;
		case 0x19: /* DIV */ POPr1 POPr2 PUSH(ps, r2 / r1) break;
		case 0x1a: /* MOD */ POPr1 POPr2 PUSH(ps, r2 % r1) break;
		case 0x1b: /* RND */ PUSH(ps, rand()) break;
		case 0x1c: /* EQU */ POPr1 POPr2 PUSH(ps, r1 == r2) break;
		case 0x1d: /* NEQ */ POPr1 POPr2 PUSH(ps, r1 != r2) break;
		case 0x1e: /* GTH */ POPr1 POPr2 PUSH(ps, r2 > r1) break;
		case 0x1f: /* LTH */ POPr1 POPr2 PUSH(ps, r2 < r1) break;
		case 0x20: /* AND */ POPr1 POPr2 PUSH(ps, r1 & r2) break;
		case 0x21: /* ORR */ POPr1 POPr2 PUSH(ps, r1 | r2) break;
		case 0x22: /* XOR */ POPr1 POPr2 PUSH(ps, r1 ^ r2) break;
		case 0x23: /* SFT */ POPr1 POPr2 PUSH(ps, (r2 >> (r1&0x0f)) << ((r1&0xf0) >> 4)) break;
		case 0x24: /* CLS */ for (r1 = 0; r1 < 32; r1++) scn[r1] = 0; break;
		case 0x25: /* SET */ POPr1 POPr2 !r1? (scn[r2 / 8] &= ~(128 >> r2 % 8)) : (scn[r2 / 8] |= (128 >> r2 % 8)); break;
		case 0x26: /* GET */ POPr1 PUSH(ps, scn[r1 / 8] & (128 >> r1 % 8) ? 1 : 0) break;
		case 0x27: /* KEY */ PUSH(ps, controller) break;
		case 0x28: /* FRM */ PUSH(ps, frame) break;
		default:
			HALT(0);
		}
	}
}

/* clang-format on */

int load(Tny *t, char *path)
{
	FILE *fp;
	long size;

	if ((fp = fopen(path, "rb")) == NULL) {
		fprintf(stderr, "Error opening file.\n");
		return 0;
	}

	fseek(fp, 0, SEEK_END);
	size = ftell(fp);
	fseek(fp, 0, SEEK_SET);

	if (size > LEN) {
		fprintf(stderr, "ROM file too large.\n");
		return 0;
	}

	fread(t->ram, sizeof(char), size, fp);
	fclose(fp);
	return 1;
}

int start(Tny *t, char *rom)
{
	if (!load(t, rom))
		return 0;
	if (!eval(t, 2))
		return 0;
	return 1;
}

void redraw()
{
	int i, j;
	SDL_Rect rect;
	rect.w = PIX_WIDTH;
	rect.h = PIX_WIDTH;
	SDL_SetRenderDrawColor(renderer, 0, 0, 0, 255);
	SDL_RenderClear(renderer);
	SDL_SetRenderDrawColor(renderer, 255, 255, 255, 255);
	for (i = 0; i < 32; i++) {
		for (j = 0; j < 8; j++) {
			if (scn[i] & (128 >> j)) {
				rect.x = (i % 2 * 8 + j) * PIX_WIDTH;
				rect.y = i / 2 * PIX_WIDTH;
				SDL_RenderFillRect(renderer, &rect);
			}
		}
	}
}

int init()
{
	if (SDL_Init(SDL_INIT_VIDEO) < 0) {
		fprintf(stderr, "Error initializing SDL: %s.\n", SDL_GetError());
		return 0;
	}

	window = SDL_CreateWindow("Tny",
		SDL_WINDOWPOS_UNDEFINED,
		SDL_WINDOWPOS_UNDEFINED,
		16 * PIX_WIDTH,
		16 * PIX_WIDTH,
		SDL_WINDOW_SHOWN | SDL_WINDOW_ALLOW_HIGHDPI);
	if (window == NULL) {
		fprintf(stderr, "Error creating window: %s.\n", SDL_GetError());
		return 0;
	}

	renderer = SDL_CreateRenderer(window, -1, 0);
	if (renderer == NULL) {
		fprintf(stderr, "Error creating renderer: %s.\n", SDL_GetError());
		return 0;
	}

	return 1;
}

void loop(Tny *t)
{
	SDL_Event e;
	Uint64 now = SDL_GetPerformanceCounter();
	Uint64 frame_interval = SDL_GetPerformanceFrequency() / 60;
	Uint64 ms_interval = SDL_GetPerformanceFrequency() / 1000;
	Uint64 frame_end;

	for (;;) {
		frame_end = now + frame_interval;

		while (SDL_PollEvent(&e) != 0) {
			if (e.type == SDL_QUIT) {
				return;
			} else if (e.type == SDL_KEYDOWN) {
				switch (e.key.keysym.sym) {
				case SDLK_UP: controller |= 0x01; break;
				case SDLK_DOWN: controller |= 0x02; break;
				case SDLK_LEFT: controller |= 0x04; break;
				case SDLK_RIGHT: controller |= 0x08; break;
				case SDLK_x: controller |= 0x10; break;
				case SDLK_c: controller |= 0x20; break;
				}
				if (e.type == SDL_KEYDOWN) {
					if (t->ram[1]) {
						if (!eval(t, t->ram[1])) return;
					}
				}
			} else if (e.type == SDL_KEYUP) {
				switch (e.key.keysym.sym) {
				case SDLK_UP: controller &= ~0x01; break;
				case SDLK_DOWN: controller &= ~0x02; break;
				case SDLK_LEFT: controller &= ~0x04; break;
				case SDLK_RIGHT: controller &= ~0x08; break;
				case SDLK_x: controller &= ~0x10; break;
				case SDLK_c: controller &= ~0x20; break;
				}
			}
		}

		if (t->ram[0]) {
			if (!eval(t, t->ram[0])) return;
		}
		frame = (frame + 1) % 60;
		redraw();
		SDL_RenderPresent(renderer);

		now = SDL_GetPerformanceCounter();
		if ((Sint64)(frame_end - now) > 0) {
			SDL_Delay((frame_end - now) / ms_interval);
			now = frame_end;
		}
	}
}

int main(int argc, char **argv)
{
	Tny t = {0};
	int i;

	srand(time(NULL));

	if (argc != 2) {
		printf("usage: tny file.rom\n");
		return 1;
	}

	if (!init())
		return 1;

	if (!start(&t, argv[1]))
		return 1;

	loop(&t);

	printf("pstack:");
	for (i = 0; i < t.ps.top; i++)
		printf("%02x", t.ps.dat[i]);

	printf("\nrstack:");
	for (i = 0; i < t.rs.top; i++)
		printf("%02x", t.rs.dat[i]);

	printf("\nscreen:");
	for (i = 0; i < 32; i++)
		printf("%d", scn[i]);

	printf("\nRAM:");
	for (i = 0; i < LEN; i++)
		printf("%02x ", t.ram[i]);

	printf("\nBuffer:");
	for (i = 0; i < LEN; i++)
		printf("%02x ", buffer[i]);

	printf("\n");

	SDL_DestroyRenderer(renderer);
	SDL_DestroyWindow(window);
	SDL_Quit();

	return 0;
}
