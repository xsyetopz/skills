# Empirical agent-reliability research intake

Reviewed on 2026-09-12 to close the supporting RESEARCH.md requirement. This
intake supplements the repository's concrete runtime counterexamples; it does
not claim a new benchmark experiment or measured skill-induced improvement.

## Package identity

Read the published USENIX Security 2025 paper, [We Have a Package for
You!][paper], with attention to its study scope and supply-chain threat model.
Its abstract reports 576,000 Python/JavaScript samples from 16 models. Those
model versions, prompts and package observations are a study sample, not current
universal hallucination rates. No aggregate percentages were imported as product
claims.

The actionable distinction is that a package name can be both plausible and
wrong, and later registry existence does not prove legitimacy. Added an
upstream-identity and supported-installation check to the existing skill-audit
workflow. This is compatible with the repository's standards-first dependency
selection, not an instruction to install every suggested package or build a new
package-verification framework.

## Long-horizon evaluation and test validity

Read [SWE-Bench Pro v2][pro], especially section 6.3, the failure-judge method,
and limitations. The study's classifications use a model judge over the final 20
turns of failed trajectories. Semantic, navigation, tool and context failures
are therefore observations under that benchmark/harness, not independently
proven causes or general rankings of current models. The paper also acknowledges
language imbalance and dependence on a finite test suite.

The maintained [evaluation repository][repository] records test removals for
outdated expectations and other harness repairs. Added revision-aware evaluation
and inspection of unexpected failures to the existing audit workflow. Retained
behavioral negative controls; no requirement to change valid tests simply
because an agent finds them inconvenient.

Narrowing repository lookups to a concrete unresolved question is recorded as an
engineering response to observed navigation/context risks. Neither paper proves
that this instruction improves the rebuilt skills. Existing practical
evaluations remain the evidence for this repository's actual changes. No
universal file-size, context-window, tool-count or complexity quota was
inferred.

## Integration and evidence limits

The reusable owner is `maintain-agent-skills`, not a new generic agent-policy
skill. Its routed audit reference now distinguishes empirical observations,
source claims and proposed mitigations. This source-only addition introduces no
runtime helper or executable asset. Validate its package structure, reference
routing and Markdown; those checks do not reproduce either study.

[paper]: https://www.usenix.org/system/files/usenixsecurity25-spracklen.pdf
[pro]: https://arxiv.org/html/2509.16941v2
[repository]: https://github.com/scaleapi/SWE-bench_Pro-os
