#include <benchmark/benchmark.h>
#include <algorithm>
#include <cstdint>
#include <string>

static void Count(benchmark::State& state, bool standard_algorithm) {
    const auto length = static_cast<std::size_t>(state.range(0));
    std::string input(length, 'x');
    for (std::size_t i = 0; i < length; i += 7) input[i] = ':';
    const auto expected = length == 0 ? 0 : (length - 1) / 7 + 1;
    for (auto _ : state) {
        (void)_;
        // Prevent an invariant result being hoisted out of the measured loop.
        benchmark::DoNotOptimize(input.data());
        benchmark::ClobberMemory();
        std::size_t count = 0;
        if (standard_algorithm) {
            count = static_cast<std::size_t>(std::count(input.begin(), input.end(), ':'));
        } else {
            for (const char value : input) count += value == ':';
        }
        benchmark::DoNotOptimize(count);
        if (count != expected) { state.SkipWithError("delimiter oracle failed"); break; }
    }
    state.SetBytesProcessed(state.iterations() * static_cast<std::int64_t>(length));
}
static void Loop(benchmark::State& state) { Count(state, false); }
static void Algorithm(benchmark::State& state) { Count(state, true); }
BENCHMARK(Loop)->Arg(16)->Arg(256)->Arg(4096);
BENCHMARK(Algorithm)->Arg(16)->Arg(256)->Arg(4096);
BENCHMARK_MAIN();
