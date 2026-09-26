// Atomics, memory order, and false sharing: references/concurrency.md
#include "harness.hpp"

#include <atomic>
#include <cstdio>
#include <memory>
#include <new>
#include <thread>
#include <vector>

extern "C" {
// seq_cst is the default order of fetch_add and operator++.
__attribute__((noinline)) long bump_seq_cst_baseline(std::atomic<long> &c) {
  return c.fetch_add(1);
}
// A pure event counter needs atomicity, not ordering.
__attribute__((noinline)) long bump_relaxed_candidate(std::atomic<long> &c) {
  return c.fetch_add(1, std::memory_order_relaxed);
}
__attribute__((noinline)) long read_seq_cst_baseline(std::atomic<long> &f) {
  return f.load();
}
__attribute__((noinline)) long read_acquire_candidate(std::atomic<long> &f) {
  return f.load(std::memory_order_acquire);
}
__attribute__((noinline)) void publish_seq_cst_baseline(std::atomic<long> &f) {
  f.store(1);
}
__attribute__((noinline)) void publish_release_candidate(std::atomic<long> &f) {
  f.store(1, std::memory_order_release);
}
}

namespace {
constexpr int kThreads = 4;
constexpr long kIters = 200'000;

// Message passing with acquire/release: the payload write happens-before
// the read that observes ready == 1.
long handoff_release_acquire() {
  long payload = 0;
  std::atomic<long> ready{0};
  std::thread producer([&] {
    payload = 42;
    publish_release_candidate(ready);
  });
  while (read_acquire_candidate(ready) == 0) {
  }
  long const seen = payload;
  producer.join();
  return seen;
}

template <class Slot> long hammer(Slot *slots) {
  std::vector<std::thread> ts;
  for (int t = 0; t < kThreads; ++t) {
    ts.emplace_back([slots, t] {
      for (long i = 0; i < kIters; ++i) {
        slots[t].n.fetch_add(1, std::memory_order_relaxed);
      }
    });
  }
  for (auto &t : ts) {
    t.join();
  }
  long s = 0;
  for (int t = 0; t < kThreads; ++t) {
    s += slots[t].n.load();
  }
  return s;
}

struct Packed {
  std::atomic<long> n{0}; // neighbours share a cache line
};
template <std::size_t Align> struct alignas(Align) Padded {
  std::atomic<long> n{0};
};
// The library constant: 256 with this toolchain on arm64 (see card).
struct Interference {
  alignas(std::hardware_destructive_interference_size) std::atomic<long> n{0};
};

template <class Slot> long run_slots() {
  std::vector<Slot> slots(kThreads);
  return hammer(slots.data());
}

long shared_atomic_total() {
  std::atomic<long> total{0};
  std::vector<std::thread> ts;
  for (int t = 0; t < kThreads; ++t) {
    ts.emplace_back([&total] {
      for (long i = 0; i < kIters; ++i) {
        total.fetch_add(1, std::memory_order_relaxed);
      }
    });
  }
  for (auto &t : ts) {
    t.join();
  }
  return total.load();
}
long local_then_combine_total() {
  std::atomic<long> total{0};
  std::vector<std::thread> ts;
  for (int t = 0; t < kThreads; ++t) {
    ts.emplace_back([&total] {
      long local = 0;
      for (long i = 0; i < kIters; ++i) {
        h::sink(local += 1); // keep the loop; no shared write inside it
      }
      total.fetch_add(local, std::memory_order_relaxed); // once per thread
    });
  }
  for (auto &t : ts) {
    t.join();
  }
  return total.load();
}
} // namespace

void verify_concurrency() {
  using h::require;
  std::atomic<long> c{0};
  bump_seq_cst_baseline(c);
  bump_relaxed_candidate(c);
  require(c.load() == 2, "counter");
  require(handoff_release_acquire() == 42, "release/acquire handoff");
  long const expect = kThreads * kIters;
  require(run_slots<Packed>() == expect, "packed total");
  require(run_slots<Padded<128>>() == expect, "padded total");
  require(run_slots<Interference>() == expect, "interference total");
  require(shared_atomic_total() == expect, "shared total");
  require(local_then_combine_total() == expect, "local total");
  std::printf("INTERFERENCE: destructive %zu, constructive %zu, "
              "sizeof Packed %zu, sizeof Interference %zu\n",
              std::hardware_destructive_interference_size,
              std::hardware_constructive_interference_size, sizeof(Packed),
              sizeof(Interference));
}

h::Pairs pairs_concurrency() {
  auto counter = std::make_shared<std::atomic<long>>(0);
  return {
      {"relaxed-counter",
       [counter] {
         for (int i = 0; i < 1000; ++i) {
           bump_seq_cst_baseline(*counter);
         }
       },
       [counter] {
         for (int i = 0; i < 1000; ++i) {
           bump_relaxed_candidate(*counter);
         }
       }},
      {"false-sharing-pad64", [] { h::sink(run_slots<Packed>()); },
       [] { h::sink(run_slots<Padded<64>>()); }},
      {"false-sharing-pad128", [] { h::sink(run_slots<Packed>()); },
       [] { h::sink(run_slots<Padded<128>>()); }},
      {"false-sharing-interference", [] { h::sink(run_slots<Packed>()); },
       [] { h::sink(run_slots<Interference>()); }},
      {"local-accumulate", [] { h::sink(shared_atomic_total()); },
       [] { h::sink(local_then_combine_total()); }},
  };
}
