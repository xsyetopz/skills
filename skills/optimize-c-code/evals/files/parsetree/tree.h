#ifndef TREE_H
#define TREE_H

#include <stddef.h>

struct tree;

/* Parses whitespace-separated decimal longs and inserts each into a binary
 * search tree in input order; equal keys go to the right subtree. Returns
 * NULL if a token is not a valid long or on allocation failure. */
struct tree *tree_parse(const char *src);

size_t tree_count(const struct tree *t);
size_t tree_height(const struct tree *t);
/* Sum of value * (in-order position + 1), with unsigned wraparound. */
unsigned long tree_checksum(const struct tree *t);
void tree_free(struct tree *t);

#endif
