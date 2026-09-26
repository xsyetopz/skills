/* Cross-TU call in a hot loop. Build with and without -flto and look for
 * "bl _lto_scale" (aarch64) or "call" to lto_scale in the linked binary. */
#include <stdio.h>
#include <stdlib.h>

int lto_scale(int x);

int main(int argc, char **argv) {
  long n = argc > 1 ? strtol(argv[1], NULL, 10) : 1000;
  long s = 0;
  for (long i = 0; i < n; ++i)
    s += lto_scale((int)(i & 0xffff));
  printf("%ld\n", s);
  return 0;
}
