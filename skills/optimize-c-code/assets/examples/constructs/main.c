/* constructs verify            oracles + deterministic count assertions
 * constructs time [filter]     clock_gettime medians per pair
 * constructs smoke             every pair once, no timing
 * constructs hot SECONDS       busy workload for sample/xctrace
 * constructs emit-{write,batched,stdio,unbuffered} LINES
 *                              whole-program output for hyperfine */
#include "bench.h"

#include <errno.h>
#include <string.h>

void join_strcat(char *out, const char *const *parts, size_t n);

static size_t parse_count(const char *s) {
  char *end = NULL;
  errno = 0;
  unsigned long v = strtoul(s, &end, 10);
  if (errno != 0 || end == s || *end != '\0' || s[0] == '-') {
    fprintf(stderr, "not a count: %s\n", s);
    exit(2);
  }
  return (size_t)v;
}

/* A deliberately quadratic loop so a sampling profiler has one obvious
 * hot frame (strcat inside join_strcat). */
static void hot(size_t seconds) {
  enum { PARTS = 8192 };
  static const char *parts[PARTS];
  static char out[PARTS * 2 + 1];
  for (size_t i = 0; i < PARTS; ++i)
    parts[i] = "ab";
  uint64_t end = now_ns() + (uint64_t)seconds * UINT64_C(1000000000);
  while (now_ns() < end) {
    join_strcat(out, parts, PARTS);
    escape(out);
  }
}

int main(int argc, char **argv) {
  const char *mode = argc > 1 ? argv[1] : "verify";
  if (strcmp(mode, "verify") == 0 && argc <= 2) {
    memory_verify();
    alloc_verify();
    codegen_verify();
    io_verify();
    puts("VERIFY PASSED");
  } else if (strcmp(mode, "smoke") == 0 && argc == 2) {
    /* Same code paths as verify; prints no timing. */
    memory_verify();
    alloc_verify();
    codegen_verify();
    io_verify();
    puts("SMOKE PASSED: every pair ran once; not a performance result");
  } else if (strcmp(mode, "time") == 0 && argc <= 3) {
    const char *filter = argc == 3 ? argv[2] : "";
    struct timespec res;
    if (clock_getres(CLOCK_MONOTONIC, &res) == 0)
      printf("CLOCK_MONOTONIC resolution %ld ns\n", res.tv_nsec);
    memory_time(filter);
    alloc_time(filter);
    codegen_time(filter);
    io_time(filter);
  } else if (strcmp(mode, "hot") == 0 && argc == 3) {
    hot(parse_count(argv[2]));
  } else if (strncmp(mode, "emit-", 5) == 0 && argc == 3) {
    if (io_emit(mode, parse_count(argv[2])) != 0) {
      fprintf(stderr, "unknown mode %s\n", mode);
      return 2;
    }
  } else {
    fputs("usage: constructs [verify|smoke|time [filter]|hot SECONDS|"
          "emit-{write,batched,stdio,unbuffered} LINES]\n",
          stderr);
    return 2;
  }
  return 0;
}
