# Verification and evidence

Select evidence at the boundary of the claim. Run the smallest sufficient set
first, then broaden only when the change crosses another contract boundary.

| Claim | Sufficient evidence | Not sufficient by itself |
| --- | --- | --- |
| Hotspot is material | Representative profile/trace/counters attributing cost and share. | Function looks slow. |
| Semantic equivalence | Independent tests/properties/differential checks for relevant partitions and errors. | Same output on one input. |
| Microbenchmark improvement | Matched complete benchmark identities, repetitions/variance, valid outputs, and same work. | Single stopwatch run. |
| Application improvement | End-to-end or component workload at actual boundary shows target metric change. | Microbenchmark only. |
| Memory improvement | Allocation and retained/live memory evidence under same workload. | Lower source allocations by inspection. |
| Concurrency/unsafe optimization safe | Race/ownership/lifetime invariants, differential checks, target/tool checks and fallback. | Comment or one green unit test. |

## Command patterns

```sh
sh assets/examples/verify.sh comparisons
sh assets/examples/verify.sh correctness 1
sh assets/examples/verify.sh reproduction
```

Bundled examples check semantic contracts and one reproduction. They are not
timing evidence for the target repository.

## Result reporting

Separate authored checks, executed checks, static analysis, simulation,
integration/host execution, production observations, skipped checks, and
unavailable checks. Include relevant failure output. A green check establishes
only the properties it can discriminate; a single flaky pass, successful parser,
or valid configuration file is not broad runtime proof.
