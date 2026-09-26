/* Signed overflow is undefined (C23 N3220 6.5.1p5). The "wrap test" below
 * is folded to 0 by the optimizer; UBSan reports the overflow at run
 * time. ckd_add/__builtin_add_overflow give a defined answer. */
#include <limits.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>

#if defined(__has_include)
#if __has_include(<stdckdint.h>) && __STDC_VERSION__ >= 202311L
#include <stdckdint.h>
#define CKD_ADD(r, a, b) ckd_add(r, a, b)
#endif
#endif
#ifndef CKD_ADD
#define CKD_ADD(r, a, b) __builtin_add_overflow(a, b, r)
#endif

__attribute__((noinline)) bool next_wraps_ub(int a) {
  return a + 1 < a; /* UB when a == INT_MAX */
}

__attribute__((noinline)) bool next_wraps_checked(int a) {
  int r;
  return CKD_ADD(&r, a, 1);
}

int main(int argc, char **argv) {
  int a = argc > 1 ? atoi(argv[1]) : INT_MAX;
  printf("checked: %d\n", next_wraps_checked(a));
  printf("ub: %d\n", next_wraps_ub(a));
  return 0;
}
