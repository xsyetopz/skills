# Bun comparison benchmark

This fixture compares linear array lookup with `Map` lookup while counting the
same deterministic keys. Both modes must produce identical JSON before timing.

```sh
./verify.sh
hyperfine --warmup 2 --runs 10 \
  'bun bench.ts red' 'bun bench.ts green'
```

`WORKLOAD_SIZE` changes the shared workload. Record `bun --version`, OS,
architecture, commands, sample count, median/mean and spread. The
candidate becomes a measured improvement only for the environment and
workload where repeated results exceed observed noise.

## Local evidence

Results below were measured on 2026-09-12 and are local evidence, not a portable
speed claim. See `measurement.txt` for the exact runtime, platform, workload,
and raw Hyperfine summary.
