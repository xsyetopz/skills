/* Code-generation pairs: aliasing, linkage, branches, loops, SIMD, and
 * checked arithmetic. verify.sh asserts instruction patterns in the -S
 * output of this file and reads its optimization record. */
#include "bench.h"

#include <ctype.h>
#include <limits.h>
#include <stdbool.h>
#include <string.h>

#if defined(__ARM_NEON) && defined(__aarch64__)
#include <arm_neon.h>
#define HAVE_NEON_A64 1
#endif

#if defined(__has_include)
#if __has_include(<stdckdint.h>) && __STDC_VERSION__ >= 202311L
#include <stdckdint.h>
#define CKD_ADD(r, a, b) ckd_add(r, a, b)
#define CKD_PATH "C23 ckd_add"
#endif
#endif
#ifndef CKD_ADD
#define CKD_ADD(r, a, b) __builtin_add_overflow(a, b, r)
#define CKD_PATH "__builtin_add_overflow"
#endif

/* ---- restrict ---- */
NOINLINE void bump_plain(int *a, int *b, const int *x) {
  *a += *x;
  *b += *x; /* x may alias a: *x is loaded again */
}

NOINLINE void bump_restrict(int *restrict a, int *restrict b,
                            const int *restrict x) {
  *a += *x;
  *b += *x; /* one load of *x suffices */
}

NOINLINE void copy_plain(unsigned char *dst, const unsigned char *src,
                         size_t n) {
  for (size_t i = 0; i < n; ++i)
    dst[i] = src[i];
}

NOINLINE void copy_restrict(unsigned char *restrict dst,
                            const unsigned char *restrict src, size_t n) {
  for (size_t i = 0; i < n; ++i)
    dst[i] = src[i];
}

NOINLINE void scale_plain(float *dst, const float *src, const float *k,
                          size_t n) {
  for (size_t i = 0; i < n; ++i)
    dst[i] = src[i] * *k;
}

NOINLINE void scale_restrict(float *restrict dst, const float *restrict src,
                             const float *restrict k, size_t n) {
  for (size_t i = 0; i < n; ++i)
    dst[i] = src[i] * *k;
}

/* ---- Internal linkage ---- */
int scale_extern(int x); /* external linkage: body must be emitted */
int scale_extern(int x) { return x * 3 + 1; }
static int scale_static(int x) { return x * 3 + 1; }

NOINLINE long apply_extern(const int *a, size_t n) {
  long s = 0;
  for (size_t i = 0; i < n; ++i)
    s += scale_extern(a[i]);
  return s;
}

NOINLINE long apply_static(const int *a, size_t n) {
  long s = 0;
  for (size_t i = 0; i < n; ++i)
    s += scale_static(a[i]);
  return s;
}

/* ---- Hoisting strlen ---- */
NOINLINE size_t count_char_strlen_cond(const char *s, char c) {
  size_t n = 0;
  for (size_t i = 0; i < strlen(s); ++i)
    n += s[i] == c;
  return n;
}

NOINLINE size_t count_char_hoisted(const char *s, char c) {
  size_t n = 0;
  size_t len = strlen(s);
  for (size_t i = 0; i < len; ++i)
    n += s[i] == c;
  return n;
}

NOINLINE void upper_strlen_cond(char *s) {
  for (size_t i = 0; i < strlen(s); ++i) /* stores to s: re-evaluated */
    s[i] = (char)toupper((unsigned char)s[i]);
}

NOINLINE void upper_hoisted(char *s) {
  size_t len = strlen(s); /* valid: toupper never produces '\0' */
  for (size_t i = 0; i < len; ++i)
    s[i] = (char)toupper((unsigned char)s[i]);
}

/* ---- Branchy vs branchless lower bound ---- */
NOINLINE size_t lower_bound_branchy(const uint32_t *a, size_t n, uint32_t key) {
  size_t lo = 0, hi = n;
  while (lo < hi) {
    size_t mid = lo + (hi - lo) / 2;
    if (a[mid] < key)
      lo = mid + 1;
    else
      hi = mid;
  }
  return lo;
}

NOINLINE size_t lower_bound_branchless(const uint32_t *a, size_t n,
                                       uint32_t key) {
  if (n == 0)
    return 0;
  const uint32_t *base = a;
  while (n > 1) {
    size_t half = n / 2;
    base = base[half - 1] < key ? base + half : base; /* csel */
    n -= half;
  }
  return (size_t)(base - a) + (*base < key);
}

/* ---- Conditional store vs unconditional select ---- */
NOINLINE void clamp_branch(int32_t *a, size_t n) {
  for (size_t i = 0; i < n; ++i)
    if (a[i] < 0)
      a[i] = 0;
}

NOINLINE void clamp_select(int32_t *a, size_t n) {
  for (size_t i = 0; i < n; ++i)
    a[i] = a[i] < 0 ? 0 : a[i]; /* writes every element */
}

/* ---- __builtin_expect on a rare error branch ---- */
NOINLINE int64_t parse_csv_plain(const char *s, size_t n) {
  uint64_t total = 0, cur = 0;
  for (size_t i = 0; i < n; ++i) {
    if (s[i] == ',') {
      total += cur;
      cur = 0;
      continue;
    }
    unsigned d = (unsigned)(unsigned char)s[i] - '0';
    if (d > 9)
      return -1;
    cur = cur * 10 + d;
  }
  return (int64_t)(total + cur);
}

NOINLINE int64_t parse_csv_expect(const char *s, size_t n) {
  uint64_t total = 0, cur = 0;
  for (size_t i = 0; i < n; ++i) {
    if (s[i] == ',') {
      total += cur;
      cur = 0;
      continue;
    }
    unsigned d = (unsigned)(unsigned char)s[i] - '0';
    if (__builtin_expect(d > 9, 0))
      return -1;
    cur = cur * 10 + d;
  }
  return (int64_t)(total + cur);
}

/* ---- Narrow element type ---- */
NOINLINE uint32_t count_at_least_i32(const int32_t *a, size_t n, int32_t t) {
  uint32_t c = 0;
  for (size_t i = 0; i < n; ++i)
    c += a[i] >= t;
  return c;
}

NOINLINE uint32_t count_at_least_u8(const uint8_t *a, size_t n, uint8_t t) {
  uint32_t c = 0;
  for (size_t i = 0; i < n; ++i)
    c += a[i] >= t;
  return c;
}

/* ---- Float reduction ---- */
NOINLINE float sum_f32_strict(const float *a, size_t n) {
  float s = 0.0f;
  for (size_t i = 0; i < n; ++i)
    s += a[i];
  return s;
}

NOINLINE float sum_f32_reassoc(const float *a, size_t n) {
#if defined(__clang__) /* other compilers keep the strict order */
#pragma clang fp reassociate(on)
#endif
  float s = 0.0f;
  for (size_t i = 0; i < n; ++i)
    s += a[i];
  return s;
}

#ifdef HAVE_NEON_A64
NOINLINE float sum_f32_neon(const float *a, size_t n) {
  float32x4_t acc0 = vdupq_n_f32(0.0f), acc1 = vdupq_n_f32(0.0f);
  size_t i = 0;
  for (; i + 8 <= n; i += 8) {
    acc0 = vaddq_f32(acc0, vld1q_f32(a + i));
    acc1 = vaddq_f32(acc1, vld1q_f32(a + i + 4));
  }
  float s = vaddvq_f32(vaddq_f32(acc0, acc1)); /* horizontal add */
  for (; i < n; ++i)                           /* scalar tail */
    s += a[i];
  return s;
}
#else
NOINLINE float sum_f32_neon(const float *a, size_t n) {
  return sum_f32_strict(a, n); /* portable fallback */
}
#endif

/* ---- Checked signed addition ---- */
/* Sum with overflow detection; returns false on overflow. */
NOINLINE bool sum_checked_precheck(const int *a, size_t n, int *out) {
  int s = 0;
  for (size_t i = 0; i < n; ++i) {
    if ((a[i] > 0 && s > INT_MAX - a[i]) || (a[i] < 0 && s < INT_MIN - a[i]))
      return false;
    s += a[i];
  }
  *out = s;
  return true;
}

NOINLINE bool sum_checked_ckd(const int *a, size_t n, int *out) {
  int s = 0;
  for (size_t i = 0; i < n; ++i)
    if (CKD_ADD(&s, s, a[i]))
      return false;
  *out = s;
  return true;
}

/* ------------------------------------------------------------------ */

static uint64_t rng(uint64_t *s) {
  *s ^= *s << 13;
  *s ^= *s >> 7;
  *s ^= *s << 17;
  return *s;
}

void codegen_verify(void) {
  uint64_t seed = 99;
  int a = 1, b = 2, x = 5;
  bump_plain(&a, &b, &x);
  check(a == 6 && b == 7, "bump_plain");
  a = 1, b = 2;
  bump_restrict(&a, &b, &x);
  check(a == 6 && b == 7, "bump_restrict");
  int y = 3;
  bump_plain(&y, &b, &y); /* aliasing call: only legal for the plain one */
  check(y == 6 && b == 13, "bump_plain aliasing call reloads *x");

  unsigned char s1[70], d1[70], d2[70];
  float f[70], g1[70], g2[70], k = 1.5f;
  for (size_t n = 0; n <= 70; ++n) {
    for (size_t i = 0; i < 70; ++i) {
      s1[i] = (unsigned char)rng(&seed);
      d1[i] = d2[i] = 0;
      f[i] = (float)(i % 13);
      g1[i] = g2[i] = -1.0f;
    }
    copy_plain(d1, s1, n);
    copy_restrict(d2, s1, n);
    check(memcmp(d1, d2, sizeof d1) == 0, "copy_restrict");
    scale_plain(g1, f, &k, n);
    scale_restrict(g2, f, &k, n);
    check(memcmp(g1, g2, sizeof g1) == 0, "scale_restrict");
    float r0 = sum_f32_strict(f, n), r1 = sum_f32_reassoc(f, n),
          r2 = sum_f32_neon(f, n);
    /* Inputs are small integers: every partial sum is exact in float, so
     * any summation order gives identical bits. */
    check(r0 == r1 && r0 == r2, "float sums (exact inputs)");
  }

  int ints[100];
  for (int i = 0; i < 100; ++i)
    ints[i] = i - 50;
  check(apply_extern(ints, 100) == apply_static(ints, 100), "linkage");

  char text[] = "a,b,,a\xc3\xa9"
                "a";
  char t1[sizeof text], t2[sizeof text];
  check(count_char_strlen_cond(text, 'a') == 3 &&
            count_char_hoisted(text, 'a') == 3,
        "count_char");
  check(count_char_hoisted("", 'a') == 0, "count_char empty");
  memcpy(t1, text, sizeof text);
  memcpy(t2, text, sizeof text);
  upper_strlen_cond(t1);
  upper_hoisted(t2);
  check(memcmp(t1, t2, sizeof t1) == 0, "upper");

  uint32_t sorted[257];
  for (size_t i = 0; i < 257; ++i)
    sorted[i] = (uint32_t)(i / 2 * 3); /* duplicates */
  for (size_t n = 0; n <= 257; ++n)
    for (uint32_t key = 0; key <= 390; ++key)
      check(lower_bound_branchy(sorted, n, key) ==
                lower_bound_branchless(sorted, n, key),
            "lower_bound for every n and key");

  int32_t c1[37], c2[37];
  for (size_t i = 0; i < 37; ++i)
    c1[i] = c2[i] = (int32_t)(rng(&seed) % 201) - 100;
  c1[0] = c2[0] = INT32_MIN;
  clamp_branch(c1, 37);
  clamp_select(c2, 37);
  check(memcmp(c1, c2, sizeof c1) == 0, "clamp");

  const char *csv[] = {"", "7", "12,30,,4", "1,x,2", ",", "9x"};
  for (size_t i = 0; i < sizeof csv / sizeof csv[0]; ++i)
    check(parse_csv_plain(csv[i], strlen(csv[i])) ==
              parse_csv_expect(csv[i], strlen(csv[i])),
          "parse_csv");
  check(parse_csv_plain("12,30,,4", 8) == 46, "parse_csv value");
  check(parse_csv_expect("1,x,2", 5) == -1, "parse_csv error");

  int32_t w[100];
  uint8_t nb[100];
  for (size_t i = 0; i < 100; ++i)
    nb[i] = (uint8_t)rng(&seed), w[i] = nb[i];
  for (size_t n = 0; n <= 100; n += 33)
    check(count_at_least_i32(w, n, 200) == count_at_least_u8(nb, n, 200),
          "count_at_least");

  int ok_in[] = {INT_MAX - 1, 1, -5, 5}, over[] = {INT_MAX, 1},
      under[] = {INT_MIN, -1};
  int r1 = 0, r2 = 0;
  check(sum_checked_precheck(ok_in, 4, &r1) && sum_checked_ckd(ok_in, 4, &r2) &&
            r1 == r2 && r1 == INT_MAX,
        "checked sum in range");
  check(!sum_checked_precheck(over, 2, &r1) && !sum_checked_ckd(over, 2, &r2),
        "checked sum overflow");
  check(!sum_checked_precheck(under, 2, &r1) && !sum_checked_ckd(under, 2, &r2),
        "checked sum underflow");
  printf("CKD path: %s\n", CKD_PATH);
  puts("PASS codegen: restrict, linkage, strlen, lower_bound, clamp, expect,"
       " narrow types, float sums, checked add");
}

/* ---- timing ---- */
struct cg_ctx {
  float *f, *g, k;
  unsigned char *src, *dst;
  uint32_t *sorted, *keys;
  int32_t *i32, *i32_work;
  uint8_t *u8;
  char *text, *csv;
  size_t n, nsorted, nkeys, ntext, ncsv;
};

static uint64_t t_scale_p(void *c) {
  struct cg_ctx *x = c;
  scale_plain(x->g, x->f, &x->k, x->n);
  escape(x->g);
  return 0;
}
static uint64_t t_scale_r(void *c) {
  struct cg_ctx *x = c;
  scale_restrict(x->g, x->f, &x->k, x->n);
  escape(x->g);
  return 0;
}
static uint64_t t_copy_p(void *c) {
  struct cg_ctx *x = c;
  copy_plain(x->dst, x->src, x->n);
  escape(x->dst);
  return 0;
}
static uint64_t t_copy_r(void *c) {
  struct cg_ctx *x = c;
  copy_restrict(x->dst, x->src, x->n);
  escape(x->dst);
  return 0;
}
static uint64_t t_cnt_cond(void *c) {
  struct cg_ctx *x = c;
  return count_char_strlen_cond(x->text, 'e');
}
static uint64_t t_cnt_hoist(void *c) {
  struct cg_ctx *x = c;
  return count_char_hoisted(x->text, 'e');
}
static uint64_t t_up_cond(void *c) {
  struct cg_ctx *x = c;
  upper_strlen_cond(x->text);
  return (uint64_t)x->text[0];
}
static uint64_t t_up_hoist(void *c) {
  struct cg_ctx *x = c;
  upper_hoisted(x->text);
  return (uint64_t)x->text[0];
}
static uint64_t t_lb_branchy(void *c) {
  struct cg_ctx *x = c;
  uint64_t s = 0;
  for (size_t i = 0; i < x->nkeys; ++i)
    s += lower_bound_branchy(x->sorted, x->nsorted, x->keys[i]);
  return s;
}
static uint64_t t_lb_branchless(void *c) {
  struct cg_ctx *x = c;
  uint64_t s = 0;
  for (size_t i = 0; i < x->nkeys; ++i)
    s += lower_bound_branchless(x->sorted, x->nsorted, x->keys[i]);
  return s;
}
static uint64_t t_clamp_b(void *c) {
  struct cg_ctx *x = c;
  memcpy(x->i32_work, x->i32, x->n * sizeof *x->i32);
  clamp_branch(x->i32_work, x->n);
  return (uint64_t)x->i32_work[1];
}
static uint64_t t_clamp_s(void *c) {
  struct cg_ctx *x = c;
  memcpy(x->i32_work, x->i32, x->n * sizeof *x->i32);
  clamp_select(x->i32_work, x->n);
  return (uint64_t)x->i32_work[1];
}
static uint64_t t_csv_p(void *c) {
  struct cg_ctx *x = c;
  return (uint64_t)parse_csv_plain(x->csv, x->ncsv);
}
static uint64_t t_csv_e(void *c) {
  struct cg_ctx *x = c;
  return (uint64_t)parse_csv_expect(x->csv, x->ncsv);
}
static uint64_t t_cnt_i32(void *c) {
  struct cg_ctx *x = c;
  return count_at_least_i32(x->i32, x->n, 200);
}
static uint64_t t_cnt_u8(void *c) {
  struct cg_ctx *x = c;
  return count_at_least_u8(x->u8, x->n, 200);
}
static uint64_t t_sum_strict(void *c) {
  struct cg_ctx *x = c;
  return (uint64_t)sum_f32_strict(x->f, 4096);
}
static uint64_t t_sum_reassoc(void *c) {
  struct cg_ctx *x = c;
  return (uint64_t)sum_f32_reassoc(x->f, 4096);
}
static uint64_t t_sum_neon(void *c) {
  struct cg_ctx *x = c;
  return (uint64_t)sum_f32_neon(x->f, 4096);
}

void codegen_time(const char *filter) {
  struct cg_ctx x = {0};
  uint64_t seed = 3;
  x.n = (size_t)1 << 20;
  x.k = 1.25f;
  x.f = calloc(x.n, sizeof *x.f);
  x.g = calloc(x.n, sizeof *x.g);
  x.src = calloc(x.n, 1);
  x.dst = calloc(x.n, 1);
  x.i32 = calloc(x.n, sizeof *x.i32);
  x.i32_work = calloc(x.n, sizeof *x.i32_work);
  x.u8 = calloc(x.n, 1);
  x.nsorted = (size_t)1 << 20;
  x.nkeys = 4096;
  x.sorted = calloc(x.nsorted, sizeof *x.sorted);
  x.keys = calloc(x.nkeys, sizeof *x.keys);
  x.ntext = 16384;
  x.text = calloc(x.ntext + 1, 1);
  x.ncsv = (size_t)1 << 20;
  x.csv = calloc(x.ncsv + 1, 1);
  check(x.f && x.g && x.src && x.dst && x.i32 && x.i32_work && x.u8 &&
            x.sorted && x.keys && x.text && x.csv,
        "alloc timing inputs");
  for (size_t i = 0; i < x.n; ++i) {
    x.f[i] = (float)(i % 13);
    x.src[i] = (unsigned char)i;
    x.u8[i] = (uint8_t)rng(&seed);
    x.i32[i] = (int32_t)(rng(&seed) % 512) - 256;
  }
  for (size_t i = 0; i < x.nsorted; ++i)
    x.sorted[i] = (uint32_t)(i * 4);
  for (size_t i = 0; i < x.nkeys; ++i)
    x.keys[i] = (uint32_t)(rng(&seed) % (x.nsorted * 4));
  for (size_t i = 0; i < x.ntext; ++i)
    x.text[i] = "abcde"[i % 5];
  for (size_t i = 0; i < x.ncsv; ++i)
    x.csv[i] = i % 4 == 3 ? ',' : (char)('0' + i % 10);
  bench_pair(filter, "restrict-scale", t_scale_p, t_scale_r, &x, 20);
  bench_pair(filter, "restrict-copy", t_copy_p, t_copy_r, &x, 20);
  bench_pair(filter, "strlen-readonly", t_cnt_cond, t_cnt_hoist, &x, 20);
  bench_pair(filter, "strlen-writes", t_up_cond, t_up_hoist, &x, 2);
  bench_pair(filter, "lower-bound", t_lb_branchy, t_lb_branchless, &x, 20);
  bench_pair(filter, "clamp", t_clamp_b, t_clamp_s, &x, 20);
  bench_pair(filter, "expect", t_csv_p, t_csv_e, &x, 20);
  bench_pair(filter, "narrow-type", t_cnt_i32, t_cnt_u8, &x, 20);
  bench_pair(filter, "float-reassoc", t_sum_strict, t_sum_reassoc, &x, 2000);
  bench_pair(filter, "float-neon", t_sum_strict, t_sum_neon, &x, 2000);
  free(x.f);
  free(x.g);
  free(x.src);
  free(x.dst);
  free(x.i32);
  free(x.i32_work);
  free(x.u8);
  free(x.sorted);
  free(x.keys);
  free(x.text);
  free(x.csv);
}
