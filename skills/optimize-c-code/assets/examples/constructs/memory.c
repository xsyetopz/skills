/* Data layout and bulk-memory pairs: baseline vs candidate. */
#include "bench.h"

#include <stdbool.h>
#include <stddef.h>
#include <string.h>

/* ---- Struct layout: order members by decreasing alignment ---- */
struct rec_padded {
  char tag;
  double value;
  char flag;
  int32_t id;
};
struct rec_packed {
  double value;
  int32_t id;
  char tag;
  char flag;
};
/* Portable guarantees only: the reordered struct is never larger and the
 * first member has offset 0. Exact sizes are printed, not assumed. */
_Static_assert(sizeof(struct rec_packed) <= sizeof(struct rec_padded),
               "reordering must not grow the record");
_Static_assert(offsetof(struct rec_packed, value) == 0, "value first");

NOINLINE double layout_sum_padded(const struct rec_padded *r, size_t n) {
  double s = 0;
  for (size_t i = 0; i < n; ++i)
    if (r[i].flag)
      s += r[i].value;
  return s;
}

NOINLINE double layout_sum_packed(const struct rec_packed *r, size_t n) {
  double s = 0;
  for (size_t i = 0; i < n; ++i)
    if (r[i].flag)
      s += r[i].value;
  return s;
}

/* ---- Array of structs vs struct of arrays ---- */
struct particle {
  float x, y, z, vx, vy, vz, mass, charge;
};

NOINLINE void advance_aos(struct particle *p, size_t n, float dt) {
  for (size_t i = 0; i < n; ++i)
    p[i].x += p[i].vx * dt;
}

NOINLINE void advance_soa(float *restrict x, const float *restrict vx, size_t n,
                          float dt) {
  for (size_t i = 0; i < n; ++i)
    x[i] += vx[i] * dt;
}

/* ---- Loop order over a row-major matrix ---- */
NOINLINE uint64_t matrix_sum_columns(const uint32_t *m, size_t rows,
                                     size_t cols) {
  uint64_t s = 0;
  for (size_t c = 0; c < cols; ++c)
    for (size_t r = 0; r < rows; ++r)
      s += m[r * cols + c];
  return s;
}

NOINLINE uint64_t matrix_sum_rows(const uint32_t *m, size_t rows, size_t cols) {
  uint64_t s = 0;
  for (size_t r = 0; r < rows; ++r)
    for (size_t c = 0; c < cols; ++c)
      s += m[r * cols + c];
  return s;
}

/* ---- memcpy / memset / memmove vs hand loops ---- */
NOINLINE void copy_loop(unsigned char *dst, const unsigned char *src,
                        size_t n) {
  for (size_t i = 0; i < n; ++i)
    dst[i] = src[i];
}

NOINLINE void copy_memcpy(unsigned char *dst, const unsigned char *src,
                          size_t n) {
  memcpy(dst, src, n);
}

NOINLINE void zero_loop(uint32_t *a, size_t n) {
  for (size_t i = 0; i < n; ++i)
    a[i] = 0;
}

NOINLINE void zero_memset(uint32_t *a, size_t n) {
  memset(a, 0, n * sizeof *a);
}

/* Shift a[0..n-2] to a[1..n-1]; the ranges overlap. */
NOINLINE void shift_loop(uint32_t *a, size_t n) {
  for (size_t i = n; i > 1; --i)
    a[i - 1] = a[i - 2];
}

NOINLINE void shift_memmove(uint32_t *a, size_t n) {
  if (n > 1)
    memmove(a + 1, a, (n - 1) * sizeof *a);
}

/* ---- Joining strings: strcat rescans, an end offset does not ---- */
NOINLINE void join_strcat(char *out, const char *const *parts, size_t n) {
  out[0] = '\0';
  for (size_t i = 0; i < n; ++i)
    strcat(out, parts[i]);
}

NOINLINE void join_offset(char *out, const char *const *parts, size_t n) {
  size_t end = 0;
  for (size_t i = 0; i < n; ++i) {
    size_t len = strlen(parts[i]);
    memcpy(out + end, parts[i], len);
    end += len;
  }
  out[end] = '\0';
}

/* ---- Remove zeros in place, keeping order ---- */
NOINLINE size_t compact_memmove(uint32_t *a, size_t n) {
  size_t i = 0;
  while (i < n) {
    if (a[i] == 0) {
      memmove(a + i, a + i + 1, (n - i - 1) * sizeof *a);
      --n; /* do not advance: the next element moved into slot i */
    } else {
      ++i;
    }
  }
  return n;
}

NOINLINE size_t compact_single_pass(uint32_t *a, size_t n) {
  size_t out = 0;
  for (size_t i = 0; i < n; ++i)
    if (a[i] != 0)
      a[out++] = a[i];
  return out;
}

/* ---- Byte histogram ---- */
NOINLINE void histogram_per_value(const unsigned char *b, size_t n,
                                  size_t out[256]) {
  for (size_t v = 0; v < 256; ++v) {
    out[v] = 0;
    for (size_t i = 0; i < n; ++i)
      out[v] += b[i] == v;
  }
}

NOINLINE void histogram_direct(const unsigned char *b, size_t n,
                               size_t out[256]) {
  memset(out, 0, 256 * sizeof out[0]);
  for (size_t i = 0; i < n; ++i)
    ++out[b[i]];
}

/* ------------------------------------------------------------------ */

static uint64_t xorshift(uint64_t *s) {
  *s ^= *s << 13;
  *s ^= *s >> 7;
  *s ^= *s << 17;
  return *s;
}

void memory_verify(void) {
  uint64_t seed = 42;
  enum { N = 1000 };

  struct rec_padded *pad = calloc(N, sizeof *pad);
  struct rec_packed *pk = calloc(N, sizeof *pk);
  check(pad && pk, "alloc layout");
  for (size_t i = 0; i < N; ++i) {
    double v = (double)(xorshift(&seed) % 1000);
    char f = (char)(i % 3 != 0);
    pad[i] = (struct rec_padded){'t', v, f, (int32_t)i};
    pk[i] = (struct rec_packed){v, (int32_t)i, 't', f};
  }
  check(layout_sum_padded(pad, N) == layout_sum_packed(pk, N),
        "layout sums equal");
  check(layout_sum_padded(pad, 0) == 0 && layout_sum_packed(pk, 0) == 0,
        "layout empty");
  printf("LAYOUT sizeof padded=%zu packed=%zu bytes\n",
         sizeof(struct rec_padded), sizeof(struct rec_packed));
  check(sizeof(struct rec_packed) < sizeof(struct rec_padded),
        "reordered record is smaller on this ABI");
  free(pad);
  free(pk);

  struct particle *ps = calloc(N, sizeof *ps);
  float *x = calloc(N, sizeof *x), *vx = calloc(N, sizeof *vx);
  check(ps && x && vx, "alloc particles");
  for (size_t i = 0; i < N; ++i) {
    ps[i].x = x[i] = (float)(xorshift(&seed) % 4096) / 8.0f;
    ps[i].vx = vx[i] = (float)(xorshift(&seed) % 4096) / 16.0f;
  }
  advance_aos(ps, N, 0.25f);
  advance_soa(x, vx, N, 0.25f);
  for (size_t i = 0; i < N; ++i)
    check(memcmp(&ps[i].x, &x[i], sizeof x[i]) == 0, "aos == soa bits");
  printf("AOS-SOA bytes per element loaded: aos=%zu (one 32-byte record)"
         " soa=%zu\n",
         sizeof(struct particle), 2 * sizeof(float));
  free(ps);
  free(x);
  free(vx);

  uint32_t m[6] = {1, 2, 3, 4, 5, 6};
  check(matrix_sum_columns(m, 2, 3) == 21 && matrix_sum_rows(m, 2, 3) == 21,
        "matrix sums");
  check(matrix_sum_rows(m, 0, 3) == 0 && matrix_sum_columns(m, 3, 0) == 0,
        "matrix empty");

  unsigned char src[67], d1[67], d2[67];
  for (size_t n = 0; n <= sizeof src; ++n) {
    for (size_t i = 0; i < sizeof src; ++i)
      src[i] = (unsigned char)(i * 7), d1[i] = d2[i] = 0xAA;
    copy_loop(d1, src, n);
    copy_memcpy(d2, src, n);
    check(memcmp(d1, d2, sizeof d1) == 0, "copy equal for every length");
  }
  uint32_t z1[33], z2[33], s1[33], s2[33];
  for (size_t n = 0; n <= 33; ++n) {
    for (size_t i = 0; i < 33; ++i)
      z1[i] = z2[i] = s1[i] = s2[i] = (uint32_t)i + 1;
    zero_loop(z1, n);
    zero_memset(z2, n);
    shift_loop(s1, n);
    shift_memmove(s2, n);
    check(memcmp(z1, z2, sizeof z1) == 0, "zero equal");
    check(memcmp(s1, s2, sizeof s1) == 0, "shift equal");
    if (n > 1)
      check(s2[0] == 1 && s2[1] == 1 && s2[n - 1] == n - 1,
            "overlapping shift keeps order (aabc, not aaaa)");
  }

  const char *parts[] = {"a", "", "\xc3\xa9", "\xf0\x9f\x99\x82", "bc"};
  char j1[32], j2[32];
  for (size_t n = 0; n <= 5; ++n) {
    join_strcat(j1, parts, n);
    join_offset(j2, parts, n);
    check(strcmp(j1, j2) == 0, "join equal");
  }
  check(strcmp(j2, "a\xc3\xa9\xf0\x9f\x99\x82"
                   "bc") == 0,
        "join expected bytes");

  /* Exhaustive over {0,1,2}^len for len <= 6: adjacent zeros included. */
  for (size_t len = 0; len <= 6; ++len) {
    size_t combos = 1;
    for (size_t i = 0; i < len; ++i)
      combos *= 3;
    for (size_t code = 0; code < combos; ++code) {
      uint32_t a[6] = {0}, b[6] = {0};
      size_t rest = code;
      for (size_t i = 0; i < len; ++i, rest /= 3)
        a[i] = b[i] = (uint32_t)(rest % 3);
      size_t na = compact_memmove(a, len), nb = compact_single_pass(b, len);
      check(na == nb && memcmp(a, b, na * sizeof a[0]) == 0,
            "compaction equal, stable order");
    }
  }

  unsigned char bytes[300];
  size_t h1[256], h2[256];
  for (size_t i = 0; i < sizeof bytes; ++i)
    bytes[i] = (unsigned char)(i * 31);
  for (size_t n = 0; n <= sizeof bytes; n += 150) {
    histogram_per_value(bytes, n, h1);
    histogram_direct(bytes, n, h2);
    check(memcmp(h1, h2, sizeof h1) == 0, "histogram equal");
  }
  puts("PASS memory: layout, aos/soa, loop order, memcpy, memset, memmove,"
       " join, compaction, histogram");
}

/* ---- timing contexts: inputs are built before timing ---- */
struct mem_ctx {
  struct rec_padded *pad;
  struct rec_packed *pk;
  struct particle *ps;
  float *x, *vx;
  uint32_t *mat, *u32, *work;
  unsigned char *src, *dst;
  const char **parts;
  char *joined;
  size_t n, rows, cols, nparts;
};

static uint64_t t_pad(void *c) {
  struct mem_ctx *m = c;
  return (uint64_t)layout_sum_padded(m->pad, m->n);
}
static uint64_t t_pk(void *c) {
  struct mem_ctx *m = c;
  return (uint64_t)layout_sum_packed(m->pk, m->n);
}
static uint64_t t_aos(void *c) {
  struct mem_ctx *m = c;
  advance_aos(m->ps, m->n, 0.0f);
  escape(m->ps);
  return 0;
}
static uint64_t t_soa(void *c) {
  struct mem_ctx *m = c;
  advance_soa(m->x, m->vx, m->n, 0.0f);
  escape(m->x);
  return 0;
}
static uint64_t t_cols(void *c) {
  struct mem_ctx *m = c;
  return matrix_sum_columns(m->mat, m->rows, m->cols);
}
static uint64_t t_rows(void *c) {
  struct mem_ctx *m = c;
  return matrix_sum_rows(m->mat, m->rows, m->cols);
}
static uint64_t t_cloop(void *c) {
  struct mem_ctx *m = c;
  copy_loop(m->dst, m->src, m->n);
  escape(m->dst);
  return m->dst[m->n - 1];
}
static uint64_t t_cmemcpy(void *c) {
  struct mem_ctx *m = c;
  copy_memcpy(m->dst, m->src, m->n);
  escape(m->dst);
  return m->dst[m->n - 1];
}
static uint64_t t_zloop(void *c) {
  struct mem_ctx *m = c;
  zero_loop(m->u32, m->n);
  escape(m->u32);
  return 0;
}
static uint64_t t_zmemset(void *c) {
  struct mem_ctx *m = c;
  zero_memset(m->u32, m->n);
  escape(m->u32);
  return 0;
}
static uint64_t t_join_cat(void *c) {
  struct mem_ctx *m = c;
  join_strcat(m->joined, m->parts, m->nparts);
  return (uint64_t)m->joined[0];
}
static uint64_t t_join_off(void *c) {
  struct mem_ctx *m = c;
  join_offset(m->joined, m->parts, m->nparts);
  return (uint64_t)m->joined[0];
}
/* Compaction mutates its input, so each call restores it first; the
 * restore (a memcpy) is identical in both variants. */
static uint64_t t_compact_mm(void *c) {
  struct mem_ctx *m = c;
  memcpy(m->work, m->u32, m->rows * sizeof *m->work);
  return compact_memmove(m->work, m->rows);
}
static uint64_t t_compact_sp(void *c) {
  struct mem_ctx *m = c;
  memcpy(m->work, m->u32, m->rows * sizeof *m->work);
  return compact_single_pass(m->work, m->rows);
}
static uint64_t t_hist_pv(void *c) {
  struct mem_ctx *m = c;
  size_t h[256];
  histogram_per_value(m->src, m->rows, h);
  return h[7];
}
static uint64_t t_hist_d(void *c) {
  struct mem_ctx *m = c;
  size_t h[256];
  histogram_direct(m->src, m->rows, h);
  return h[7];
}

void memory_time(const char *filter) {
  struct mem_ctx m = {0};
  uint64_t seed = 7;
  m.n = (size_t)1 << 20;
  m.pad = calloc(m.n, sizeof *m.pad);
  m.pk = calloc(m.n, sizeof *m.pk);
  m.ps = calloc(m.n, sizeof *m.ps);
  m.x = calloc(m.n, sizeof *m.x);
  m.vx = calloc(m.n, sizeof *m.vx);
  m.u32 = calloc(m.n, sizeof *m.u32);
  m.work = calloc(m.n, sizeof *m.work);
  m.src = calloc(m.n, 1);
  m.dst = calloc(m.n, 1);
  m.rows = m.cols = 2048;
  m.mat = calloc(m.rows * m.cols, sizeof *m.mat);
  m.nparts = 4096;
  m.parts = calloc(m.nparts, sizeof *m.parts);
  m.joined = calloc(m.nparts * 2 + 1, 1);
  check(m.pad && m.pk && m.ps && m.x && m.vx && m.u32 && m.work && m.src &&
            m.dst && m.mat && m.parts && m.joined,
        "alloc timing inputs");
  for (size_t i = 0; i < m.n; ++i) {
    m.pad[i].value = m.pk[i].value = (double)(i % 97);
    m.pad[i].flag = m.pk[i].flag = (char)(i & 1);
    m.src[i] = (unsigned char)xorshift(&seed);
  }
  for (size_t i = 0; i < m.rows * m.cols; ++i)
    m.mat[i] = (uint32_t)i;
  for (size_t i = 0; i < m.nparts; ++i)
    m.parts[i] = "ab";
  bench_pair(filter, "layout", t_pad, t_pk, &m, 10);
  bench_pair(filter, "aos-soa", t_aos, t_soa, &m, 10);
  bench_pair(filter, "loop-order", t_cols, t_rows, &m, 2);
  bench_pair(filter, "memcpy", t_cloop, t_cmemcpy, &m, 20);
  bench_pair(filter, "memset", t_zloop, t_zmemset, &m, 20);
  bench_pair(filter, "join", t_join_cat, t_join_off, &m, 2);
  /* compaction: 16384 elements, one third zeros */
  m.rows = 16384;
  for (size_t i = 0; i < m.rows; ++i)
    m.u32[i] = (uint32_t)(i % 3);
  bench_pair(filter, "compaction", t_compact_mm, t_compact_sp, &m, 4);
  m.rows = 65536;
  bench_pair(filter, "histogram", t_hist_pv, t_hist_d, &m, 2);
  free(m.pad);
  free(m.pk);
  free(m.ps);
  free(m.x);
  free(m.vx);
  free(m.u32);
  free(m.work);
  free(m.src);
  free(m.dst);
  free(m.mat);
  free(m.parts);
  free(m.joined);
}
