#include "tree.h"

#include <stdio.h>
#include <stdlib.h>

int main(int argc, char **argv)
{
    FILE *in = argc > 1 ? fopen(argv[1], "rb") : stdin;
    if (in == NULL) {
        perror(argv[1]);
        return 1;
    }
    size_t cap = 1 << 16, len = 0;
    char *buf = malloc(cap);
    size_t got;
    while (buf != NULL && (got = fread(buf + len, 1, cap - len - 1, in)) > 0) {
        len += got;
        if (cap - len < 2) {
            char *grown = realloc(buf, cap * 2);
            if (grown == NULL)
                free(buf);
            buf = grown;
            cap *= 2;
        }
    }
    if (buf == NULL)
        return 1;
    buf[len] = '\0';
    struct tree *t = tree_parse(buf);
    free(buf);
    if (t == NULL) {
        fputs("parse error\n", stderr);
        return 1;
    }
    printf("count=%zu height=%zu checksum=%lu\n", tree_count(t), tree_height(t), tree_checksum(t));
    tree_free(t);
    return 0;
}
