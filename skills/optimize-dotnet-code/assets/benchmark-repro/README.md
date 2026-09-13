# .NET comparison benchmark

This fixture compares repeated immutable-string concatenation with one
`StringBuilder` for the same deterministic inputs. The verification script
requires identical length and checksum before timing.

```sh
./verify.sh
hyperfine --warmup 2 --runs 10 \
  'dotnet ./bin/Release/net10.0/Benchmark.dll red' \
  'dotnet ./bin/Release/net10.0/Benchmark.dll green'
```

Set `WORKLOAD_SIZE` identically for both commands. Record `dotnet --info`, build
configuration, OS, architecture, sample count, and spread. Exact local results
are in `measurement.txt`; they are evidence only for that measured workload.
