#include "tree.h"

#include <ctype.h>
#include <errno.h>
#include <stdlib.h>

struct node {
    long value;
    struct node *left;
    struct node *right;
};

struct tree {
    struct node *root;
    size_t count;
};

static void free_nodes(struct node *n)
{
    if (n == NULL)
        return;
    free_nodes(n->left);
    free_nodes(n->right);
    free(n);
}

void tree_free(struct tree *t)
{
    if (t == NULL)
        return;
    free_nodes(t->root);
    free(t);
}

static int insert(struct tree *t, long value)
{
    struct node *n = malloc(sizeof *n);
    if (n == NULL)
        return -1;
    n->value = value;
    n->left = n->right = NULL;
    struct node **link = &t->root;
    while (*link != NULL)
        link = value < (*link)->value ? &(*link)->left : &(*link)->right;
    *link = n;
    t->count++;
    return 0;
}

struct tree *tree_parse(const char *src)
{
    struct tree *t = malloc(sizeof *t);
    if (t == NULL)
        return NULL;
    t->root = NULL;
    t->count = 0;
    const char *p = src;
    for (;;) {
        while (isspace((unsigned char)*p))
            p++;
        if (*p == '\0')
            return t;
        char *end;
        errno = 0;
        long v = strtol(p, &end, 10);
        if (end == p || errno == ERANGE || (*end != '\0' && !isspace((unsigned char)*end)) ||
            insert(t, v) != 0) {
            tree_free(t);
            return NULL;
        }
        p = end;
    }
}

size_t tree_count(const struct tree *t)
{
    return t->count;
}

static size_t height(const struct node *n)
{
    if (n == NULL)
        return 0;
    size_t l = height(n->left), r = height(n->right);
    return 1 + (l > r ? l : r);
}

size_t tree_height(const struct tree *t)
{
    return height(t->root);
}

static void walk(const struct node *n, unsigned long *pos, unsigned long *sum)
{
    if (n == NULL)
        return;
    walk(n->left, pos, sum);
    *sum += (unsigned long)n->value * ++*pos;
    walk(n->right, pos, sum);
}

unsigned long tree_checksum(const struct tree *t)
{
    unsigned long pos = 0, sum = 0;
    walk(t->root, &pos, &sum);
    return sum;
}
