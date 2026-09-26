// Deterministic allocation and ARC counters for macOS.
//
// Malloc: replaces the function pointers of malloc_zones[0] (the default
// zone) after making its page writable with vm_protect. The page is left
// writable: restoring read-only protection crashed xzone malloc on macOS 27.
//
// ARC: the Swift runtime routes swift_retain/swift_release through the
// _swift_retain/_swift_release function pointers only after the
// Instruments-only flag below is set. package-benchmark uses the same hooks
// (Sources/SwiftRuntimeHooks/shims.c) for its retainCount/releaseCount
// metrics. These are private runtime symbols: use them in test binaries
// only, never in shipping code.
#include "ccount.h"

#include <mach/mach.h>
#include <malloc/malloc.h>
#include <stdatomic.h>
#include <stdbool.h>
#include <stddef.h>

static _Atomic uint64_t mallocs, retains, releases;

typedef void *(*m_fn)(malloc_zone_t *, size_t);
typedef void *(*c_fn)(malloc_zone_t *, size_t, size_t);
typedef void *(*r_fn)(malloc_zone_t *, void *, size_t);
typedef void *(*tm_fn)(malloc_zone_t *, size_t, malloc_type_id_t);
typedef void *(*tc_fn)(malloc_zone_t *, size_t, size_t, malloc_type_id_t);
typedef void *(*tr_fn)(malloc_zone_t *, void *, size_t, malloc_type_id_t);
static m_fn om;
static c_fn oc, oa;
static r_fn orl;
static tm_fn otm;
static tc_fn otc, ota;
static tr_fn otr;

static void *hm(malloc_zone_t *z, size_t s) {
  mallocs++;
  return om(z, s);
}
static void *hc(malloc_zone_t *z, size_t n, size_t s) {
  mallocs++;
  return oc(z, n, s);
}
static void *ha(malloc_zone_t *z, size_t a, size_t s) {
  mallocs++;
  return oa(z, a, s);
}
static void *hr(malloc_zone_t *z, void *p, size_t s) {
  mallocs++;
  return orl(z, p, s);
}
static void *htm(malloc_zone_t *z, size_t s, malloc_type_id_t t) {
  mallocs++;
  return otm(z, s, t);
}
static void *htc(malloc_zone_t *z, size_t n, size_t s, malloc_type_id_t t) {
  mallocs++;
  return otc(z, n, s, t);
}
static void *hta(malloc_zone_t *z, size_t a, size_t s, malloc_type_id_t t) {
  mallocs++;
  return ota(z, a, s, t);
}
static void *htr(malloc_zone_t *z, void *p, size_t s, malloc_type_id_t t) {
  mallocs++;
  return otr(z, p, s, t);
}

int ccount_install_malloc(void) {
  vm_address_t *zones = NULL;
  unsigned count = 0;
  if (malloc_get_all_zones(mach_task_self(), NULL, &zones, &count) != 0 ||
      count == 0) {
    return 1;
  }
  malloc_zone_t *z = (malloc_zone_t *)zones[0];
  if (vm_protect(mach_task_self(), (vm_address_t)z, sizeof(*z), 0,
                 VM_PROT_READ | VM_PROT_WRITE) != KERN_SUCCESS) {
    return 2;
  }
  om = z->malloc;
  z->malloc = hm;
  oc = z->calloc;
  z->calloc = hc;
  orl = z->realloc;
  z->realloc = hr;
  if (z->version >= 5 && z->memalign) {
    oa = z->memalign;
    z->memalign = ha;
  }
  if (z->version >= 16) {
    if (z->malloc_type_malloc) {
      otm = z->malloc_type_malloc;
      z->malloc_type_malloc = htm;
    }
    if (z->malloc_type_calloc) {
      otc = z->malloc_type_calloc;
      z->malloc_type_calloc = htc;
    }
    if (z->malloc_type_realloc) {
      otr = z->malloc_type_realloc;
      z->malloc_type_realloc = htr;
    }
    if (z->malloc_type_memalign) {
      ota = z->malloc_type_memalign;
      z->malloc_type_memalign = hta;
    }
  }
  return 0;
}

uint64_t ccount_mallocs(void) { return mallocs; }

uint64_t ccount_bytes_in_use(void) {
  malloc_statistics_t stats;
  malloc_zone_statistics(NULL, &stats);
  return stats.size_in_use;
}

typedef struct HeapObject HeapObject;
#define SWIZZLE_FLAG                                                           \
  _swift_enableSwizzlingOfAllocationAndRefCountingFunctions_forInstrumentsOnly
extern bool SWIZZLE_FLAG;
extern HeapObject *(*_swift_retain)(HeapObject *);
extern HeapObject *(*_swift_release)(HeapObject *);
extern HeapObject *(*_swift_tryRetain)(HeapObject *);
extern HeapObject *(*_swift_retain_n)(HeapObject *, uint32_t);
extern HeapObject *(*_swift_release_n)(HeapObject *, uint32_t);

static HeapObject *(*oret)(HeapObject *);
static HeapObject *(*orel)(HeapObject *);
static HeapObject *(*otry)(HeapObject *);
static HeapObject *(*oretn)(HeapObject *, uint32_t);
static HeapObject *(*oreln)(HeapObject *, uint32_t);

static HeapObject *hret(HeapObject *o) {
  retains++;
  return oret(o);
}
static HeapObject *hrel(HeapObject *o) {
  releases++;
  return orel(o);
}
static HeapObject *htry(HeapObject *o) {
  HeapObject *r = otry(o);
  if (r) {
    retains++;
  }
  return r;
}
static HeapObject *hretn(HeapObject *o, uint32_t n) {
  retains += n;
  return oretn(o, n);
}
static HeapObject *hreln(HeapObject *o, uint32_t n) {
  releases += n;
  return oreln(o, n);
}

void ccount_install_arc(void) {
  SWIZZLE_FLAG = true;
  oret = _swift_retain;
  _swift_retain = hret;
  orel = _swift_release;
  _swift_release = hrel;
  otry = _swift_tryRetain;
  _swift_tryRetain = htry;
  oretn = _swift_retain_n;
  _swift_retain_n = hretn;
  oreln = _swift_release_n;
  _swift_release_n = hreln;
}

uint64_t ccount_retains(void) { return retains; }
uint64_t ccount_releases(void) { return releases; }
