/* Allocation-strategy pairs. Code under test allocates through the
 * counting wrappers in count.h so the oracle can assert call counts. */
#include "bench.h"
#include "count.h"

#include <stdalign.h>
#include <string.h>

/* ---- Arena (bump) allocator ---- */
struct arena_block {
  struct arena_block *next;
  size_t used, cap;
  alignas(max_align_t) unsigned char data[];
};

struct arena {
  struct arena_block *head;
  size_t block_size;
};

static void *arena_alloc(struct arena *a, size_t size) {
  size_t align = alignof(max_align_t);
  if (size > SIZE_MAX - sizeof(struct arena_block) - (align - 1))
    return NULL; /* rounding or the block header would wrap */
  size = (size + align - 1) & ~(align - 1);
  struct arena_block *b = a->head;
  if (b == NULL || b->cap - b->used < size) {
    size_t cap = size > a->block_size ? size : a->block_size;
    b = cm_malloc(sizeof *b + cap);
    if (b == NULL)
      return NULL;
    b->next = a->head;
    b->used = 0;
    b->cap = cap;
    a->head = b;
  }
  void *p = b->data + b->used;
  b->used += size;
  return p;
}

static void arena_free_all(struct arena *a) {
  while (a->head != NULL) {
    struct arena_block *next = a->head->next;
    cm_free(a->head);
    a->head = next;
  }
}

struct node {
  uint64_t value;
  struct node *next;
};

/* Build a list of n nodes, sum it, release it. */
NOINLINE uint64_t list_malloc(size_t n) {
  struct node *head = NULL;
  for (size_t i = 0; i < n; ++i) {
    struct node *x = cm_malloc(sizeof *x);
    check(x != NULL, "node alloc");
    *x = (struct node){i, head};
    head = x;
  }
  uint64_t s = 0;
  while (head != NULL) {
    struct node *next = head->next;
    s += head->value;
    cm_free(head);
    head = next;
  }
  return s;
}

NOINLINE uint64_t list_arena(size_t n) {
  struct arena a = {NULL, 64 * 1024};
  struct node *head = NULL;
  for (size_t i = 0; i < n; ++i) {
    struct node *x = arena_alloc(&a, sizeof *x);
    check(x != NULL, "arena alloc");
    *x = (struct node){i, head};
    head = x;
  }
  uint64_t s = 0;
  for (; head != NULL; head = head->next)
    s += head->value;
  arena_free_all(&a); /* one free per block, not per node */
  return s;
}

/* ---- Free list of fixed-size slots ---- */
union slot {
  union slot *next_free;
  struct node node;
};

struct pool {
  union slot *free;
  struct arena backing;
};

static struct node *pool_get(struct pool *p) {
  union slot *s = p->free;
  if (s != NULL)
    p->free = s->next_free;
  else
    s = arena_alloc(&p->backing, sizeof *s);
  return s == NULL ? NULL : &s->node;
}

static void pool_put(struct pool *p, struct node *n) {
  union slot *s = (union slot *)n;
  s->next_free = p->free;
  p->free = s;
}

/* Churn: keep a window of `live` nodes, replace the oldest `ops` times. */
NOINLINE uint64_t churn_malloc(size_t live, size_t ops) {
  struct node *ring[64] = {0};
  uint64_t s = 0;
  for (size_t i = 0; i < ops; ++i) {
    size_t k = i % live;
    if (ring[k] != NULL) {
      s += ring[k]->value;
      cm_free(ring[k]);
    }
    ring[k] = cm_malloc(sizeof *ring[k]);
    check(ring[k] != NULL, "churn alloc");
    ring[k]->value = i;
  }
  for (size_t k = 0; k < live; ++k)
    cm_free(ring[k]);
  return s;
}

NOINLINE uint64_t churn_pool(size_t live, size_t ops) {
  struct pool p = {NULL, {NULL, 4096}};
  struct node *ring[64] = {0};
  uint64_t s = 0;
  for (size_t i = 0; i < ops; ++i) {
    size_t k = i % live;
    if (ring[k] != NULL) {
      s += ring[k]->value;
      pool_put(&p, ring[k]);
    }
    ring[k] = pool_get(&p);
    check(ring[k] != NULL, "pool alloc");
    ring[k]->value = i;
  }
  arena_free_all(&p.backing);
  return s;
}

/* ---- Dynamic array growth ---- */
struct u32vec {
  uint32_t *data;
  size_t len, cap;
};

static int push_grow_by_one(struct u32vec *v, uint32_t x) {
  if (v->len == v->cap) {
    uint32_t *d = cm_realloc(v->data, (v->cap + 1) * sizeof *d);
    if (d == NULL)
      return -1; /* old block still valid and owned by v */
    v->data = d;
    v->cap += 1;
  }
  v->data[v->len++] = x;
  return 0;
}

static int push_grow_double(struct u32vec *v, uint32_t x) {
  if (v->len == v->cap) {
    size_t cap = v->cap ? v->cap * 2 : 16;
    if (cap > SIZE_MAX / sizeof *v->data)
      return -1;
    uint32_t *d = cm_realloc(v->data, cap * sizeof *d);
    if (d == NULL)
      return -1;
    v->data = d;
    v->cap = cap;
  }
  v->data[v->len++] = x;
  return 0;
}

NOINLINE uint64_t fill_grow_by_one(size_t n) {
  struct u32vec v = {0};
  for (size_t i = 0; i < n; ++i)
    check(push_grow_by_one(&v, (uint32_t)i) == 0, "push");
  uint64_t s = v.len ? v.data[v.len - 1] + v.len : 0;
  cm_free(v.data);
  return s;
}

NOINLINE uint64_t fill_grow_double(size_t n) {
  struct u32vec v = {0};
  for (size_t i = 0; i < n; ++i)
    check(push_grow_double(&v, (uint32_t)i) == 0, "push");
  uint64_t s = v.len ? v.data[v.len - 1] + v.len : 0;
  cm_free(v.data);
  return s;
}

/* ------------------------------------------------------------------ */

static unsigned long calls(void) { return cm.mallocs + cm.reallocs; }

static void report(const char *name, unsigned long base, unsigned long cand) {
  printf("ALLOC %-12s baseline %6lu calls  candidate %6lu calls\n", name, base,
         cand);
  check(cand < base, name);
}

void alloc_verify(void) {
  static const size_t sizes[] = {0, 1, 2, 1000, 5000};
  unsigned long b = 0, c = 0;
  for (size_t i = 0; i < sizeof sizes / sizeof sizes[0]; ++i) {
    size_t n = sizes[i];
    cm_reset();
    uint64_t rb = list_malloc(n);
    b = calls();
    check(cm.frees == cm.mallocs, "list_malloc frees every node");
    cm_reset();
    uint64_t rc = list_arena(n);
    c = calls();
    check(cm.frees == cm.mallocs, "arena frees every block");
    check(rb == rc && rb == (n ? (uint64_t)n * (n - 1) / 2 : 0), "list sums");
  }
  report("arena", b, c);

  for (size_t live = 1; live <= 64; live *= 4) {
    cm_reset();
    uint64_t rb = churn_malloc(live, 10000);
    b = calls();
    cm_reset();
    uint64_t rc = churn_pool(live, 10000);
    c = calls();
    check(rb == rc, "churn sums");
    check(cm.frees == cm.mallocs, "pool frees backing blocks");
  }
  report("free-list", b, c);

  for (size_t i = 0; i < sizeof sizes / sizeof sizes[0]; ++i) {
    size_t n = sizes[i];
    cm_reset();
    uint64_t rb = fill_grow_by_one(n);
    b = calls();
    cm_reset();
    uint64_t rc = fill_grow_double(n);
    c = calls();
    check(rb == rc, "growth results");
  }
  report("growth", b, c);
  puts("PASS alloc: arena, free list, geometric growth");
}

static uint64_t t_list_m(void *c) { return list_malloc(*(size_t *)c); }
static uint64_t t_list_a(void *c) { return list_arena(*(size_t *)c); }
static uint64_t t_churn_m(void *c) { return churn_malloc(64, *(size_t *)c); }
static uint64_t t_churn_p(void *c) { return churn_pool(64, *(size_t *)c); }
static uint64_t t_grow_1(void *c) { return fill_grow_by_one(*(size_t *)c); }
static uint64_t t_grow_2(void *c) { return fill_grow_double(*(size_t *)c); }

void alloc_time(const char *filter) {
  size_t n = 100000;
  bench_pair(filter, "arena", t_list_m, t_list_a, &n, 5);
  bench_pair(filter, "free-list", t_churn_m, t_churn_p, &n, 5);
  bench_pair(filter, "growth", t_grow_1, t_grow_2, &n, 5);
}
