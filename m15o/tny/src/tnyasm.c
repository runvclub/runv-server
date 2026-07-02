#include <stdio.h>
#include <ctype.h>
#include <string.h>

#define TOKEN_LEN 16

const char *mnemonics[] = {"BRK", "RET", "JMP", "JMR", "JCN", "JCR", "LIT", "POP", "DUP", "SWP", "ROT", "OVR", "PSH", "PUL", "RSI", "RSJ", "STA", "LDA", "STB", "LDB", "ADD", "SUB", "INC", "DEC", "MUL", "DIV", "MOD", "RND", "EQU", "NEQ", "GTH", "LTH", "AND", "ORR", "XOR", "SFT", "CLS", "SET", "GET", "KEY", "FRM"};

unsigned char mnlen = sizeof(mnemonics) / sizeof(char *);

/* trim: trim spaces */
int trim(FILE *fp)
{
	char c;

	while ((c = fgetc(fp)) != EOF && isspace(c))
		;

	if (c != EOF) {
		ungetc(c, fp);
	}

	return c;
}

/* readtoken: read next token from file; return EOF to indicate end */
int readtoken(char *token, FILE *fp)
{
	int i;
	int c;

	if (trim(fp) == EOF)
		return EOF;

	for (i = 0; i < TOKEN_LEN - 1 && (c = fgetc(fp)) != EOF && !isspace(c); i++) {
		token[i] = c;
	}

	token[i] = '\0';

	return 1;
}

/* nextoken: get next token; return EOF to indicate end */
int nextoken(char *t, FILE *fp)
{
	int c;

	c = readtoken(t, fp);
	if (t[0] == '#') {
		while ((c = fgetc(fp)) != EOF && c != '\n')
			;
		c = nextoken(t, fp);
	}

	return c;
}

/* islabel: check if token is a label */
int islabel(char *t)
{
	return t[strlen(t) - 1] == ':';
}

/* getopcode: return the opcode associated with token; -1 if not found */
int getopcode(char *t)
{
	int i;

	for (i = 0; i < mnlen; i++) {
		if (strcmp(t, mnemonics[i]) == 0)
			return i;
	}

	return -1;
}

int getsym(char *t, char (*symbols)[16])
{
	int i;

	for (i = 0; i < 256; i++) {
		if (strcmp(symbols[i], t) == 0)
			return i;
	}

	return -1;
}

int main(int argc, char **argv)
{
	FILE *fp;
	char token[TOKEN_LEN];
	char symbols[256][TOKEN_LEN] = {0};
	unsigned char rom[256] = {0};
	int i, op;
	unsigned int v;

	if (argc != 3) {
		printf("usage: input.tny output.rom\n");
		return 1;
	}

	if ((fp = fopen(argv[1], "r")) == NULL) {
		fprintf(stderr, "Error opening source file\n");
		return 1;
	}

	i = 0;

	/* Find labels */
	while (nextoken(token, fp) != EOF && i < 256) {
		if (islabel(token)) {
			token[strlen(token) - 1] = '\0';
			strcpy(symbols[i], token);
		} else {
			i++;
		}
	}

	if (i == 256 && !feof(fp)) {
		fprintf(stderr, "Too many instructions\n");
		return 1;
	}

	if (fseek(fp, 0, SEEK_SET) != 0) {
		fprintf(stderr, "Error seeking back to start of file\n");
		return 1;
	}

	i = 0;

	/* assemble */
	while (nextoken(token, fp) != EOF) {
		if (islabel(token))
			continue;
		else if (token[0] == '@' && (v = getsym(token + 1, symbols)) != -1) {
			rom[i++] = v;
		} else if ((op = getopcode(token)) != -1) {
			rom[i++] = op;
		} else if (strlen(token) < 3 && sscanf(token, "%2x", &v) == 1) {
			rom[i++] = v;
		} else {
			fprintf(stderr, "Unknown token: %s\n", token);
			fclose(fp);
			return 1;
		}
	}

	fclose(fp);

	/* output */
	if ((fp = fopen(argv[2], "wb")) == NULL) {
		fprintf(stderr, "error opening output file\n");
		return 1;
	}

	if (fwrite(rom, 1, i, fp) != i) {
		fprintf(stderr, "error writing rom\n");
		return 1;
	}

	fclose(fp);

	return 0;
}
