// Shared measurement harness for the construct catalog.
//
// - alloc_calls(): global operator new calls (harness.cpp replaces every
//   replaceable allocation function, including aligned and nothrow forms).
// - sink()/clobber(): Google Benchmark style optimization barriers.
// - Tracked<NoexceptMove>: counts copies and moves.
// - time_pairs(): std::chrono median timing of baseline/candidate pairs.
#pragma once

#include <cstddef>
#include <functional>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace h {

// Number of global operator new calls since process start.
long alloc_calls();

// Allocation calls performed while running f. The result of f is sunk so
// the optimizer cannot elide a new/delete pair whose result is unused.
template <class F> long allocs(F &&f) {
  long const before = alloc_calls();
  f();
  return alloc_calls() - before;
}

// Force value to be materialized; the asm is opaque to the optimizer.
template <class T> inline void sink(T const &value) {
  asm volatile("" : : "r,m"(value) : "memory");
}
template <class T> inline void sink(T &value) {
  asm volatile("" : "+r,m"(value) : : "memory");
}
// Force pending writes to memory that has escaped through sink().
inline void clobber() { asm volatile("" : : : "memory"); }

struct Counts {
  long copies = 0;
  long moves = 0;
};
extern Counts tracked;
inline void reset_tracked() { tracked = Counts{}; }

// Value type that counts copy and move operations. NoexceptMove selects
// whether the move constructor is declared noexcept.
template <bool NoexceptMove> struct Tracked {
  int value = 0;
  Tracked() = default;
  explicit Tracked(int v) : value(v) {}
  Tracked(Tracked const &other) : value(other.value) { ++tracked.copies; }
  Tracked(Tracked &&other) noexcept(NoexceptMove) : value(other.value) {
    ++tracked.moves;
  }
  Tracked &operator=(Tracked const &other) {
    value = other.value;
    ++tracked.copies;
    return *this;
  }
  Tracked &operator=(Tracked &&other) noexcept(NoexceptMove) {
    value = other.value;
    ++tracked.moves;
    return *this;
  }
  friend bool operator==(Tracked const &, Tracked const &) = default;
};
using Item = Tracked<true>;

[[noreturn]] void fail(std::string_view message);
inline void require(bool condition, std::string_view message) {
  if (!condition) {
    fail(message);
  }
}

// Prints "KIND name: baseline -> candidate" and requires candidate to be
// strictly lower. Use for deterministic benefit assertions.
void less(char const *kind, char const *name, long base, long cand);
// Prints the same line but requires equality: a measured "no difference".
void same(char const *kind, char const *name, long base, long cand);

struct Pair {
  char const *name;
  std::function<void()> base;
  std::function<void()> cand;
};
using Pairs = std::vector<Pair>;

// Median and minimum ns per call over 31 samples; each sample runs a
// batch sized so it takes at least 200 us.
void time_pairs(Pairs const &pairs, std::string_view filter);
// Runs every pair once (smoke test, no timing).
void smoke_pairs(Pairs const &pairs);

} // namespace h
