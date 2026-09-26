/* Counting allocation wrappers: code under test calls cm_* instead of
 * malloc/realloc/free so the oracle can assert call counts. Test-only
 * instrumentation; not thread-safe. */
#ifndef COUNT_H
#define COUNT_H

#include <stddef.h>

struct cm_counts {
  unsigned long mallocs;
  unsigned long reallocs;
  unsigned long frees;
};

extern struct cm_counts cm;

void cm_reset(void);
void *cm_malloc(size_t size);
void *cm_realloc(void *ptr, size_t size);
void cm_free(void *ptr);

#endif
