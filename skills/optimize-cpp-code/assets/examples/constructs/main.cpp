// constructs verify         equivalence + allocation/copy/move oracles
// constructs smoke          run every pair once; no timing
// constructs time [filter]  std::chrono median timing of every pair
// constructs print-endl|print-newline|print-sync|print-nosync|
//            print-format|print-print|print-snprintf|print-to-chars N
//                           stdout writers for hyperfine (io.md)
#include "harness.hpp"

#include <cstdio>
#include <cstdlib>
#include <string_view>

void verify_objects();
h::Pairs pairs_objects();
void verify_containers();
h::Pairs pairs_containers();
void verify_codegen();
h::Pairs pairs_codegen();
void verify_io();
h::Pairs pairs_io();
int run_printer(std::string_view mode, long rows);
void verify_concurrency();
h::Pairs pairs_concurrency();

namespace {
h::Pairs all_pairs() {
  h::Pairs all;
  for (auto make : {pairs_objects, pairs_containers, pairs_codegen, pairs_io,
                    pairs_concurrency}) {
    for (auto &p : make()) {
      all.push_back(std::move(p));
    }
  }
  return all;
}
} // namespace

int main(int argc, char **argv) {
  std::string_view const mode = argc > 1 ? argv[1] : "verify";
  if (mode == "verify") {
    verify_objects();
    verify_containers();
    verify_codegen();
    verify_io();
    verify_concurrency();
    std::puts("VERIFY PASSED");
    return 0;
  }
  if (mode == "smoke") {
    h::smoke_pairs(all_pairs());
    return 0;
  }
  if (mode == "time") {
    h::time_pairs(all_pairs(), argc > 2 ? argv[2] : "");
    return 0;
  }
  if (mode.starts_with("print-") && argc == 3) {
    return run_printer(mode, std::atol(argv[2]));
  }
  std::fputs("usage: constructs verify|smoke|time [filter]|print-* N\n",
             stderr);
  return 2;
}
