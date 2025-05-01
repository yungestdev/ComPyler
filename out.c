#include <stdio.h>
#include <stdlib.h>
#include <string.h>

struct Pointr {
    int x;
    int y;
};

void Pointr___init__(struct Pointr* self, int x, int y) {
    self->x = x;
    self->y = y;
}

void Pointr_print(struct Pointr* self) {
    printf("%d %d", self->x, self->y);
}

void main() {
    struct Pointr* tmp_pointr = malloc(sizeof(struct Pointr));
    Pointr___init__(tmp_pointr, 3, 4);
    struct Pointr* p = tmp_pointr;
    Pointr_print(p);
}

