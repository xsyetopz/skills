/* Runtime CPU dispatch for x86-64: an AVX2 clone of a loop plus a
 * baseline clone, selected once with __builtin_cpu_supports. On AArch64
 * NEON is part of the base ISA (ACLE: __ARM_NEON is always 1), so only
 * the portable function is built. */
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>

static uint32_t sum_portable(const uint32_t *a, size_t n) {
  uint32_t s = 0;
  for (size_t i = 0; i < n; ++i)
    s += a[i];
  return s;
}

#if defined(__x86_64__) && (defined(__clang__) || defined(__GNUC__))
__attribute__((target("avx2"))) static uint32_t sum_avx2(const uint32_t *a,
                                                         size_t n) {
  uint32_t s = 0; /* same source; compiled with AVX2 enabled */
  for (size_t i = 0; i < n; ++i)
    s += a[i];
  return s;
}

typedef uint32_t (*sum_fn)(const uint32_t *, size_t);

static sum_fn pick_sum(void) {
  __builtin_cpu_init(); /* needed only before constructors run */
  return __builtin_cpu_supports("avx2") ? sum_avx2 : sum_portable;
}
#else
typedef uint32_t (*sum_fn)(const uint32_t *, size_t);
static sum_fn pick_sum(void) { return sum_portable; }
#endif

uint32_t sum_dispatch(const uint32_t *a, size_t n);

uint32_t sum_dispatch(const uint32_t *a, size_t n) {
  static sum_fn fn; /* resolved once; single-threaded example */
  if (fn == NULL)
    fn = pick_sum();
  return fn(a, n);
}

int main(void) {
  uint32_t a[100];
  for (uint32_t i = 0; i < 100; ++i)
    a[i] = i;
  uint32_t s = sum_dispatch(a, 100);
  printf("%u\n", s);
  return s == 4950 ? 0 : 1;
}
