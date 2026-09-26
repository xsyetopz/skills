// libc++ hardening mode: built twice by verify.sh (hardening mode).
//   -D_LIBCPP_HARDENING_MODE=_LIBCPP_HARDENING_MODE_NONE
//   -D_LIBCPP_HARDENING_MODE=_LIBCPP_HARDENING_MODE_FAST
// hardening sum N    sums v[idx[i]] N times (timed with hyperfine)
// hardening oob      reads one element past the end: traps under FAST,
//                    undefined behavior under NONE (never run it there)
#include <cstdio>
#include <cstdlib>
#include <string_view>
#include <vector>

extern "C" __attribute__((noinline)) long
gather_sum(std::vector<long> const &v, std::vector<unsigned> const &idx) {
  long s = 0;
  for (auto i : idx) {
    s += v[i]; // FAST mode: bounds check + trap before the load
  }
  return s;
}

int main(int argc, char **argv) {
  std::string_view const mode = argc > 1 ? argv[1] : "";
  std::vector<long> v(4096);
  std::vector<unsigned> idx(4096);
  for (unsigned i = 0; i < 4096; ++i) {
    v[i] = i;
    idx[i] = (i * 2654435761U) % 4096;
  }
  if (mode == "sum" && argc == 3) {
    long const n = std::atol(argv[2]);
    long s = 0;
    for (long r = 0; r < n; ++r) {
      s += gather_sum(v, idx);
    }
    std::printf("%ld\n", s);
    return s == n * (4095L * 4096 / 2) ? 0 : 1;
  }
  if (mode == "oob") {
    idx.back() = 4096; // one past the end
    std::printf("%ld\n", gather_sum(v, idx));
    return 0;
  }
  std::fputs("usage: hardening sum N | oob\n", stderr);
  return 2;
}
