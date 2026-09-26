/* Skewed branch workload for profile-guided optimization. The input is
 * generated from a seed so every run sees the same distribution: about
 * 1 in 64 bytes is a digit, the rest are spread over the other classes. */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

enum { N = 1 << 20 };
static unsigned char buf[N];

__attribute__((noinline)) static uint64_t classify(const unsigned char *b,
                                                   size_t n) {
  uint64_t digits = 0, upper = 0, lower = 0, space = 0, other = 0;
  for (size_t i = 0; i < n; ++i) {
    unsigned c = b[i];
    if (c >= '0' && c <= '9')
      digits += c;
    else if (c >= 'A' && c <= 'Z')
      upper += c;
    else if (c >= 'a' && c <= 'z')
      lower += c;
    else if (c == ' ')
      space++;
    else
      other ^= c;
  }
  return digits * 31 + upper * 17 + lower * 7 + space * 3 + other;
}

int main(int argc, char **argv) {
  long reps = argc > 1 ? strtol(argv[1], NULL, 10) : 50;
  uint64_t s = 88172645463325252u, total = 0;
  for (size_t i = 0; i < N; ++i) {
    s ^= s << 13, s ^= s >> 7, s ^= s << 17;
    unsigned r = (unsigned)(s % 64);
    buf[i] = r == 0   ? (unsigned char)('0' + s % 10)
             : r < 40 ? (unsigned char)('a' + s % 26)
             : r < 50 ? ' '
             : r < 60 ? (unsigned char)('A' + s % 26)
                      : (unsigned char)(s >> 8);
  }
  for (long r = 0; r < reps; ++r) {
    /* Barrier: classify only reads buf, so without this the optimizer may
     * call it once and reuse the result for every repetition. */
    __asm__ volatile("" : : : "memory");
    total += classify(buf, N);
  }
  printf("%llu\n", (unsigned long long)total);
  return 0;
}
