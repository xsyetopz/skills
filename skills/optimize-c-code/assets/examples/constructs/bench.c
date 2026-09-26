#include "bench.h"
#include "count.h"

#include <stdlib.h>
#include <string.h>

volatile uint64_t bench_sink;
struct cm_counts cm;

void cm_reset(void) { memset(&cm, 0, sizeof cm); }

void *cm_malloc(size_t size) {
  ++cm.mallocs;
  return malloc(size);
}

void *cm_realloc(void *ptr, size_t size) {
  ++cm.reallocs;
  return realloc(ptr, size);
}

void cm_free(void *ptr) {
  if (ptr != NULL)
    ++cm.frees;
  free(ptr);
}

void check(int ok, const char *what) {
  if (!ok) {
    fprintf(stderr, "FAIL %s\n", what);
    exit(1);
  }
}

static int cmp_u64(const void *a, const void *b) {
  uint64_t x = *(const uint64_t *)a, y = *(const uint64_t *)b;
  return (x > y) - (x < y);
}

uint64_t bench_median_ns(bench_fn f, void *ctx, unsigned reps,
                         unsigned samples) {
  uint64_t per_call[64];
  if (samples > 64)
    samples = 64;
  for (unsigned s = 0; s < samples; ++s) {
    uint64_t start = now_ns();
    for (unsigned r = 0; r < reps; ++r)
      bench_sink += f(ctx);
    per_call[s] = (now_ns() - start) / reps;
  }
  qsort(per_call, samples, sizeof per_call[0], cmp_u64);
  return per_call[samples / 2];
}

void bench_pair(const char *filter, const char *name, bench_fn base,
                bench_fn cand, void *ctx, unsigned reps) {
  if (filter != NULL && filter[0] != '\0' && strstr(name, filter) == NULL)
    return;
  bench_sink += base(ctx) + cand(ctx); /* warm caches and page tables */
  uint64_t b = bench_median_ns(base, ctx, reps, 21);
  uint64_t c = bench_median_ns(cand, ctx, reps, 21);
  printf("TIME %-18s baseline %10llu ns  candidate %10llu ns\n", name,
         (unsigned long long)b, (unsigned long long)c);
  fflush(stdout);
}
