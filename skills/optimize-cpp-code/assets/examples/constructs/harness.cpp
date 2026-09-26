#include "harness.hpp"

#include <algorithm>
#include <atomic>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <new>

namespace {
std::atomic<long> g_calls{0};

void *counted_alloc(std::size_t size) {
  g_calls.fetch_add(1, std::memory_order_relaxed);
  if (void *p = std::malloc(size == 0 ? 1 : size)) {
    return p;
  }
  throw std::bad_alloc{};
}

void *counted_aligned(std::size_t size, std::align_val_t align) {
  g_calls.fetch_add(1, std::memory_order_relaxed);
  auto const a = std::max(static_cast<std::size_t>(align), sizeof(void *));
  void *p = nullptr;
  if (posix_memalign(&p, a, size == 0 ? 1 : size) != 0) {
    throw std::bad_alloc{};
  }
  return p;
}
} // namespace

// Every replaceable global allocation function ([new.delete]). Missing one
// form (for example the aligned overloads used by std::pmr and over-aligned
// types) would make counts disagree between new and delete.
void *operator new(std::size_t n) { return counted_alloc(n); }
void *operator new[](std::size_t n) { return counted_alloc(n); }
void *operator new(std::size_t n, std::nothrow_t const &) noexcept {
  try {
    return counted_alloc(n);
  } catch (...) {
    return nullptr;
  }
}
void *operator new[](std::size_t n, std::nothrow_t const &) noexcept {
  try {
    return counted_alloc(n);
  } catch (...) {
    return nullptr;
  }
}
void *operator new(std::size_t n, std::align_val_t a) {
  return counted_aligned(n, a);
}
void *operator new[](std::size_t n, std::align_val_t a) {
  return counted_aligned(n, a);
}
void *operator new(std::size_t n, std::align_val_t a,
                   std::nothrow_t const &) noexcept {
  try {
    return counted_aligned(n, a);
  } catch (...) {
    return nullptr;
  }
}
void *operator new[](std::size_t n, std::align_val_t a,
                     std::nothrow_t const &) noexcept {
  try {
    return counted_aligned(n, a);
  } catch (...) {
    return nullptr;
  }
}
void operator delete(void *p) noexcept { std::free(p); }
void operator delete[](void *p) noexcept { std::free(p); }
void operator delete(void *p, std::size_t) noexcept { std::free(p); }
void operator delete[](void *p, std::size_t) noexcept { std::free(p); }
void operator delete(void *p, std::nothrow_t const &) noexcept { std::free(p); }
void operator delete[](void *p, std::nothrow_t const &) noexcept {
  std::free(p);
}
void operator delete(void *p, std::align_val_t) noexcept { std::free(p); }
void operator delete[](void *p, std::align_val_t) noexcept { std::free(p); }
void operator delete(void *p, std::size_t, std::align_val_t) noexcept {
  std::free(p);
}
void operator delete[](void *p, std::size_t, std::align_val_t) noexcept {
  std::free(p);
}
void operator delete(void *p, std::align_val_t,
                     std::nothrow_t const &) noexcept {
  std::free(p);
}
void operator delete[](void *p, std::align_val_t,
                       std::nothrow_t const &) noexcept {
  std::free(p);
}

namespace h {

Counts tracked;

long alloc_calls() { return g_calls.load(std::memory_order_relaxed); }

void fail(std::string_view message) {
  std::fprintf(stderr, "FAIL: %.*s\n", static_cast<int>(message.size()),
               message.data());
  std::exit(1);
}

// Under AddressSanitizer the runtime interposes operator new, so calls
// made inside libc++.dylib bypass the counting replacement. verify.sh
// sanitize sets CONSTRUCTS_NO_COUNTS=1 to keep the equality oracles and
// skip the count assertions there.
bool counts_enforced() {
  static bool const enforced = std::getenv("CONSTRUCTS_NO_COUNTS") == nullptr;
  return enforced;
}

void less(char const *kind, char const *name, long base, long cand) {
  std::printf("%s %s: %ld -> %ld\n", kind, name, base, cand);
  if (counts_enforced() && !(cand < base)) {
    fail(std::string(kind) + " " + name + ": candidate not lower");
  }
}

void same(char const *kind, char const *name, long base, long cand) {
  std::printf("%s %s: %ld -> %ld (no difference expected)\n", kind, name, base,
              cand);
  if (counts_enforced() && cand != base) {
    fail(std::string(kind) + " " + name + ": expected equal counts");
  }
}

namespace {
using Clock = std::chrono::steady_clock;

double ns_per_call(std::function<void()> const &f, long batch) {
  auto const start = Clock::now();
  for (long i = 0; i < batch; ++i) {
    f();
  }
  std::chrono::duration<double, std::nano> const d = Clock::now() - start;
  return d.count() / static_cast<double>(batch);
}

struct Timing {
  double median;
  double min;
};

Timing measure(std::function<void()> const &f) {
  long batch = 1;
  // Calibrate (also serves as warm-up): grow until a batch takes 200 us.
  while (ns_per_call(f, batch) * static_cast<double>(batch) < 200'000.0 &&
         batch < (1L << 24)) {
    batch *= 2;
  }
  std::vector<double> samples;
  for (int i = 0; i < 31; ++i) {
    samples.push_back(ns_per_call(f, batch));
  }
  std::sort(samples.begin(), samples.end());
  return {samples[samples.size() / 2], samples.front()};
}
} // namespace

void time_pairs(Pairs const &pairs, std::string_view filter) {
  for (auto const &p : pairs) {
    if (!filter.empty() &&
        std::string_view(p.name).find(filter) == std::string_view::npos) {
      continue;
    }
    auto const b = measure(p.base);
    auto const c = measure(p.cand);
    std::printf("TIME %s: baseline median %.1f ns (min %.1f), candidate "
                "median %.1f ns (min %.1f)\n",
                p.name, b.median, b.min, c.median, c.min);
  }
}

void smoke_pairs(Pairs const &pairs) {
  for (auto const &p : pairs) {
    p.base();
    p.cand();
  }
  std::printf("SMOKE: %zu pairs ran once each; not a timing result\n",
              pairs.size());
}

} // namespace h
