/* Output buffering pairs. A custom FILE whose write callback counts calls
 * shows how many times stdio hands data to the OS for each buffer mode:
 * funopen on macOS/BSD, fopencookie on glibc. */
#if defined(__linux__)
#define _GNU_SOURCE
#endif
#include "bench.h"

#include <errno.h>
#include <fcntl.h>
#include <string.h>
#include <unistd.h>

struct write_stats {
  unsigned long calls;
  unsigned long bytes;
  uint64_t hash; /* FNV-1a of every byte, in order */
};

static void account(struct write_stats *st, const char *buf, size_t n) {
  st->calls++;
  st->bytes += n;
  for (size_t i = 0; i < n; ++i)
    st->hash = (st->hash ^ (unsigned char)buf[i]) * UINT64_C(1099511628211);
}

#if defined(__GLIBC__)
static ssize_t cookie_write(void *c, const char *buf, size_t n) {
  account(c, buf, n);
  return (ssize_t)n;
}
static FILE *counting_file(struct write_stats *st) {
  cookie_io_functions_t io = {NULL, cookie_write, NULL, NULL};
  return fopencookie(st, "w", io);
}
#else
static int cookie_write(void *c, const char *buf, int n) {
  account(c, buf, (size_t)n);
  return n;
}
static FILE *counting_file(struct write_stats *st) {
  return funopen(st, NULL, cookie_write, NULL, NULL);
}
#endif

/* Write `lines` CSV records through a FILE in the given buffer mode. */
static struct write_stats stdio_records(int mode, size_t size, size_t lines) {
  struct write_stats st = {0, 0, UINT64_C(14695981039346656037)};
  FILE *f = counting_file(&st);
  check(f != NULL, "counting FILE");
  /* setvbuf must be the first operation on the stream. */
  check(setvbuf(f, NULL, mode, size) == 0, "setvbuf");
  for (size_t i = 0; i < lines; ++i)
    check(fprintf(f, "%zu,%zu\n", i, i * 7 % 1000) > 0, "fprintf");
  check(fclose(f) == 0, "fclose flushes");
  return st;
}

/* ---- write(2) per record vs one write per filled buffer ---- */
typedef void (*sink_fn)(void *ctx, const char *buf, size_t n);

static int format_record(char *out, size_t cap, size_t i) {
  return snprintf(out, cap, "%zu,%zu\n", i, i * 7 % 1000);
}

NOINLINE void emit_per_record(sink_fn sink, void *ctx, size_t lines) {
  char rec[64];
  for (size_t i = 0; i < lines; ++i) {
    int n = format_record(rec, sizeof rec, i);
    sink(ctx, rec, (size_t)n);
  }
}

NOINLINE void emit_batched(sink_fn sink, void *ctx, size_t lines) {
  static char buf[65536];
  size_t used = 0;
  for (size_t i = 0; i < lines; ++i) {
    if (sizeof buf - used < 64) {
      sink(ctx, buf, used);
      used = 0;
    }
    used += (size_t)format_record(buf + used, sizeof buf - used, i);
  }
  if (used != 0)
    sink(ctx, buf, used);
}

static void write_all(int fd, const char *buf, size_t n) {
  while (n > 0) { /* write(2) may be partial or interrupted */
    ssize_t w = write(fd, buf, n);
    if (w < 0 && errno == EINTR)
      continue;
    check(w > 0, "write");
    buf += w;
    n -= (size_t)w;
  }
}

static void sink_stats(void *ctx, const char *buf, size_t n) {
  account(ctx, buf, n);
}
static void sink_fd(void *ctx, const char *buf, size_t n) {
  write_all(*(int *)ctx, buf, n);
}

void io_verify(void) {
  static const size_t sizes[] = {0, 1, 1000, 20000};
  for (size_t k = 0; k < sizeof sizes / sizeof sizes[0]; ++k) {
    size_t lines = sizes[k];
    struct write_stats un = stdio_records(_IONBF, 0, lines),
                       ln = stdio_records(_IOLBF, 4096, lines),
                       fu = stdio_records(_IOFBF, 65536, lines);
    check(un.bytes == fu.bytes && un.hash == fu.hash && ln.hash == fu.hash,
          "identical bytes in every buffer mode");
    struct write_stats a = {0, 0, UINT64_C(14695981039346656037)};
    struct write_stats b = a;
    emit_per_record(sink_stats, &a, lines);
    emit_batched(sink_stats, &b, lines);
    check(a.bytes == b.bytes && a.hash == b.hash && a.hash == fu.hash,
          "batched emit: identical bytes");
    if (lines == 20000) {
      printf("STDIO %lu bytes: _IONBF %lu calls, _IOLBF %lu calls,"
             " _IOFBF(64 KiB) %lu calls\n",
             fu.bytes, un.calls, ln.calls, fu.calls);
      printf("WRITE per-record %lu calls, batched(64 KiB) %lu calls\n", a.calls,
             b.calls);
      check(fu.calls < ln.calls && ln.calls <= un.calls,
            "full < line <= unbuffered");
      check(b.calls < a.calls, "batched < per-record");
    }
  }
  puts("PASS io: setvbuf modes and batched writes produce identical bytes");
}

struct io_ctx {
  int fd;
  size_t lines;
};

static uint64_t t_per_record(void *c) {
  struct io_ctx *x = c;
  emit_per_record(sink_fd, &x->fd, x->lines);
  return 0;
}
static uint64_t t_batched(void *c) {
  struct io_ctx *x = c;
  emit_batched(sink_fd, &x->fd, x->lines);
  return 0;
}

void io_time(const char *filter) {
  struct io_ctx x = {open("/dev/null", O_WRONLY), 20000};
  check(x.fd >= 0, "open /dev/null");
  bench_pair(filter, "write-batching", t_per_record, t_batched, &x, 3);
  close(x.fd);
}

/* Whole-program variants for hyperfine and output comparison. */
int io_emit(const char *variant, size_t lines) {
  int fd = STDOUT_FILENO;
  if (strcmp(variant, "emit-write") == 0) {
    emit_per_record(sink_fd, &fd, lines);
  } else if (strcmp(variant, "emit-batched") == 0) {
    emit_batched(sink_fd, &fd, lines);
  } else if (strcmp(variant, "emit-unbuffered") == 0 ||
             strcmp(variant, "emit-stdio") == 0) {
    if (variant[5] == 'u')
      check(setvbuf(stdout, NULL, _IONBF, 0) == 0, "setvbuf stdout");
    for (size_t i = 0; i < lines; ++i)
      printf("%zu,%zu\n", i, i * 7 % 1000);
    check(fflush(stdout) == 0, "fflush");
  } else {
    return 2;
  }
  return 0;
}
