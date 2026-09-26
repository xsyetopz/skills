# Go performance result

## Target

- Objective and metric: <ns/op | p99 latency | allocs/op | live heap | RSS>
- Workload and input: <benchmark name, input size, representative source>
- Toolchain: <go version>, <GOOS/GOARCH>, CPU <model>, `go` directive <x>
- Runtime settings: GOGC <v>, GOMEMLIMIT <v>, GOMAXPROCS <v>, PGO <on/off>

## Attribution

- Profile command: <go test ... -cpuprofile/-memprofile ...>
- Finding: <function, flat/cum %, alloc_space share, or trace observation>

## Change

- Construct card: <reference file and card name>
- Use when conditions met: <evidence>
- Do not use when conditions excluded: <evidence>
- Compiler evidence (if the card names one): <-m / -m=2 / check_bce lines>

## Correctness

- Oracle: <test name and command>, result <pass/fail>
- Edge cases: <empty, boundary, error, aliasing, ordering, nil vs empty>
- Race: <go test -race command>, result <pass/fail>

## Measurement

- Command: <go test -run '^$' -bench X -benchmem -count 10 ...>
- benchstat:

```text
<paste the benchstat table: sec/op, B/op, allocs/op with p and n>
```

- Application-level result: <load test, hyperfine, service metric>

## Decision

- Keep, revert, or inconclusive: <decision and reason>
- Not verified: <other platforms, production profile, container limits>
