// Parallel algorithms. libc++ ships them behind -fexperimental-library;
// verify.sh builds this file with that flag (parallel mode).
#include <algorithm>
#include <chrono>
#include <cstdio>
#include <execution>
#include <functional>
#include <numeric>
#include <vector>

namespace {
template <class F> double median_ms(F f) {
  std::vector<double> t;
  for (int i = 0; i < 9; ++i) {
    asm volatile("" : : : "memory"); // no hoisting across repetitions
    auto const s = std::chrono::steady_clock::now();
    f();
    std::chrono::duration<double, std::milli> const d =
        std::chrono::steady_clock::now() - s;
    t.push_back(d.count());
  }
  std::sort(t.begin(), t.end());
  return t[t.size() / 2];
}
std::vector<unsigned> input(std::size_t n) {
  std::vector<unsigned> v(n);
  unsigned x = 12345;
  for (auto &e : v) {
    x = x * 1664525U + 1013904223U;
    e = x;
  }
  return v;
}
} // namespace

int main() {
  for (std::size_t n :
       {std::size_t{1000}, std::size_t{100000}, std::size_t{10000000}}) {
    auto const base = input(n);
    // Oracle: identical sorted output and identical sums.
    auto a = base;
    auto b = base;
    std::sort(a.begin(), a.end());
    std::sort(std::execution::par, b.begin(), b.end());
    if (a != b) {
      std::puts("FAIL: par sort differs");
      return 1;
    }
    auto const expect = std::accumulate(base.begin(), base.end(), 0ULL);
    // Hazard: reduce may combine two elements with plus<>, giving an
    // unsigned (32-bit) partial sum that wraps before widening to init's
    // type ([numerics.defns] GENERALIZED_SUM). Record, do not assert.
    auto const naive =
        std::reduce(std::execution::par, base.begin(), base.end(), 0ULL);
    auto const naive_seq = std::reduce(base.begin(), base.end(), 0ULL);
    std::printf("PAR n=%zu: reduce(par, unsigned, 0ULL) %s accumulate; "
                "reduce(unsigned, 0ULL) without policy %s\n",
                n, naive == expect ? "equals" : "DIFFERS FROM",
                naive_seq == expect ? "equals" : "DIFFERS");
    auto const widened = std::transform_reduce(
        std::execution::par, base.begin(), base.end(), 0ULL,
        std::plus<unsigned long long>{},
        [](unsigned x) { return static_cast<unsigned long long>(x); });
    if (widened != expect) {
      std::puts("FAIL: widened par transform_reduce differs");
      return 1;
    }
    double const sort_seq = median_ms([&] {
      auto w = base;
      std::sort(w.begin(), w.end());
    });
    double const sort_par = median_ms([&] {
      auto w = base;
      std::sort(std::execution::par, w.begin(), w.end());
    });
    unsigned long long sink = 0;
    auto const widen = [](unsigned x) {
      return static_cast<unsigned long long>(x);
    };
    double const red_seq = median_ms([&] {
      asm volatile("" : : "r"(base.data()) : "memory");
      sink += std::transform_reduce(base.begin(), base.end(), 0ULL,
                                    std::plus<>{}, widen);
    });
    double const red_par = median_ms([&] {
      asm volatile("" : : "r"(base.data()) : "memory");
      sink += std::transform_reduce(std::execution::par, base.begin(),
                                    base.end(), 0ULL, std::plus<>{}, widen);
    });
    std::printf("PAR n=%zu: sort seq %.4f ms par %.4f ms; "
                "transform_reduce seq %.4f ms par %.4f ms (sink %llu)\n",
                n, sort_seq, sort_par, red_seq, red_par, sink % 10);
  }
  std::puts("PARALLEL PASSED: par results equal seq results");
  return 0;
}
