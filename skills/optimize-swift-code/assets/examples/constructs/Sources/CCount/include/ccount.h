#ifndef CCOUNT_H
#define CCOUNT_H
#include <stdint.h>

// Wraps the allocation entry points of the default malloc zone. Call once,
// before measuring. Returns 0 on success.
int ccount_install_malloc(void);
// Total malloc/calloc/realloc/memalign calls (including typed variants).
uint64_t ccount_mallocs(void);

// Enables the Swift runtime's Instruments-only swizzling switch and wraps
// swift_retain/swift_release (and the _n and tryRetain variants).
void ccount_install_arc(void);
uint64_t ccount_retains(void);
uint64_t ccount_releases(void);

// Bytes currently allocated in all malloc zones (malloc_zone_statistics).
uint64_t ccount_bytes_in_use(void);
#endif
