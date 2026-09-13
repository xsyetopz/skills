# Rust comparison benchmark

This fixture compares repeated linear lookup with `HashMap` lookup while
counting the same deterministic integers. Sorting occurs only in the candidate
to make its result order comparable; correctness is checked before timing.

```sh
./verify.sh
hyperfine --warmup 2 --runs 10 \
  './target/release/rust-skill-benchmark red' \
  './target/release/rust-skill-benchmark green'
```

Set `WORKLOAD_SIZE` for both commands to alter the shared workload. Record
`rustc -Vv`, build profile, OS, architecture, samples, and spread. Treat the
result as local workload evidence only. Exact local results are in
`measurement.txt`.
