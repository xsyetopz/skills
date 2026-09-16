# Performance result

Objective and workload: actual metric, input distribution and required behavior.
Identity: baseline/candidate revisions, toolchain, runtime, flags, CPU/OS,
concurrency. Attributed cost: profile evidence, inclusive/self costs, relevant
allocation/retention. Change: mechanism and why it should affect that cost;
complexity/ownership tradeoff. Correctness: independent expected-result check,
boundary and error cases, cancellation/lifetime checks. Measurement: exact
commands, warmup/process/sample policy, raw native result locations. Result:
matched identities, units, effect and variability; regressions and inconclusive
cases. Separate startup from steady state and instrumentation from
uninstrumented runs. Decision: keep/reject/inconclusive under the actual
objective. No unsupported global claim such as “zero allocation” or “lock-free”;
state the tested scope.
