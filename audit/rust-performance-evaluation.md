# Rust performance evaluation

Evaluated 2026-09-12. Explicit-only `optimize-rust-code` replaces
`rust-performance`. Twelve inherited reference files were consolidated into two;
all fragments were inspected before removal. Removed a non-compiling SIMD sketch
with undefined implementations rather than present it as an executable example.

## Source intake and corrections

Selected chapters from `rust-performance-research.zip` covered evidence,
provenance, unsafe testing, SIMD/floats, embedded targets, API design, memory
hierarchy, security, regression gates and C/C++ comparison contracts. Relevant
claims were checked against Rust Reference layout/undefined behavior, standard
pointer, float, architecture, allocator and collection documentation, and
Cargo/rustc profile documentation. Sources are linked from the references.

Imported numerical equivalence, invalid-reference/provenance, panic/drop,
volatile-versus-synchronization and memory-retention boundaries. Rejected the
source's suggestion that trait objects stabilize plugin ABIs. Did not import its
SIMD dot product as an equivalent scalar replacement: the reduction order
changes floating-point results. No universal performance thresholds, allocator
changes, new pool framework or dependency inventory rankings were adopted. Other
archive material remains available for selective intake; this is not a
whole-archive validation claim.

## Executable line-reading example

Extracted the reference example into `/tmp/rust-lines-evidence/lines.rs`.
Rustfmt and `rustc --edition 2024 --test -D warnings` passed on Rust 1.98.1,
Apple arm64. Two behavior tests passed: exact empty/Unicode/CRLF/blank/final
unterminated record preservation, and invalid UTF-8 error propagation after a
successful earlier callback. No allocation count or speedup was measured here.

## Actual Cargo profiling and PGO

`/tmp/rust-pgo-evidence` contains a small numeric-record analyzer and training/
held-out inputs. Both release and custom profiling builds passed with locked
Cargo input. The profiling profile retained line-table debug information.

Installed rustup stable's `llvm-tools-preview`, then selected its matching
`llvm-profdata` explicitly: PATH initially selected Swift's LLVM tool while
`rustc` selected Homebrew. Both Rust compilers reported 1.98.1/LLVM 22.1.8; PGO
used rustup consistently. Updated instructions explain matching tool lookup.

Generate, train, merge and profile-use phases ran for aarch64-apple-darwin.
Merged data contained twelve functions. The final compiler emitted one missing
profile warning for `std::rt::lang_start`; it was retained, not suppressed.
Held-out output matched the baseline exactly: `3 2 4294967394`. This verifies
PGO command behavior and this output, not complete training coverage or a PGO
speedup. The documented Linux target was not executed on Linux.

## Independent optimization evaluation

A fresh-context evaluator received ordered duplicate elimination for thousands
of event keys, including attacker-controlled input. It replaced repeated linear
scans with a standard randomized `HashSet<&str>` and retained independently
owned output strings in first-occurrence order. No custom hasher, unsafe code,
dependency, API change or parallelism was introduced.

On 12,000 inputs with 8,000 distinct keys, 36 post-first samples per version had
medians 59.742 ms baseline and 0.302 ms candidate, about 198 times faster for
this workload. Ranges were 59.226–60.281 ms and 0.289–0.616 ms. Candidate tails
are retained in the evidence, not discarded as inconvenient samples. Input
construction and result destruction were outside the timed interval.

Evaluator release tests, formatting and Clippy with warnings denied passed.
Integration inspected code and benchmark; the benchmark's checksum counted
entries rather than validating contents. Added 200 deterministic comparisons
against complete ordered reference outputs; the release differential test
passed. Existing contract tests cover distinct Unicode encodings and output
ownership.

Preallocation reserves total input count, trading memory for growth avoidance;
it is not a universal choice for duplicate-heavy inputs. Guidance now calls out
that distribution explicitly. No memory profile, collision stress test, Miri,
sanitizer, hardware-counter or cross-target result is claimed for this safe-only
change. Artifact: `/tmp/rust-opt-forward-work.ZkUc2X`; evaluator report:
`/tmp/rust-opt-forward-result.md`.

## Package verification

Official skills-ref and skill-creator validators passed. Strict Markdown and
local reference resolution passed. Invocation metadata requires explicit named
use; specialized optimization is not selected merely from a Rust keyword.
