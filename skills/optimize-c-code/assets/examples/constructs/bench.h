/* Timing harness, optimization barrier, and oracle helpers.
 * POSIX clock_gettime(CLOCK_MONOTONIC); GNU C inline asm for the barrier
 * (GCC and Clang). */
#ifndef BENCH_H
#define BENCH_H

#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define NOINLINE __attribute__((noinline))

/* Monotonic nanoseconds. CLOCK_MONOTONIC cannot be set, so wall-clock
 * adjustments do not distort intervals. */
static inline uint64_t now_ns(void) {
  struct timespec ts;
  if (clock_gettime(CLOCK_MONOTONIC, &ts) != 0)
    abort();
  return (uint64_t)ts.tv_sec * UINT64_C(1000000000) + (uint64_t)ts.tv_nsec;
}

/* Optimization barrier: the compiler must assume the asm reads *p and
 * any memory, so stores feeding p cannot be deleted or hoisted out of the
 * timed loop. Emits no instructions. */
static inline void escape(const void *p) {
  __asm__ volatile("" : : "r"(p) : "memory");
}

/* Results go here so the measured work stays observable. */
extern volatile uint64_t bench_sink;

typedef uint64_t (*bench_fn)(void *ctx);

/* Median ns per call over `samples` batches of `reps` calls. */
uint64_t bench_median_ns(bench_fn f, void *ctx, unsigned reps,
                         unsigned samples);

/* Prints "TIME name: baseline X ns, candidate Y ns" when name contains
 * filter (NULL or "" runs all). Runs both once first as a warm-up. */
void bench_pair(const char *filter, const char *name, bench_fn base,
                bench_fn cand, void *ctx, unsigned reps);

/* Oracle assertion: prints and exits 1 on failure. */
void check(int ok, const char *what);

/* Each module exposes verify (oracle + deterministic metric) and time. */
void memory_verify(void);
void memory_time(const char *filter);
void alloc_verify(void);
void alloc_time(const char *filter);
void codegen_verify(void);
void codegen_time(const char *filter);
void io_verify(void);
void io_time(const char *filter);
int io_emit(const char *variant, size_t lines);

#endif
