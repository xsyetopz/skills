# C semantic traps

Performance work is incorrect when it changes a supported result, error,
ownership/lifetime, ordering, concurrency, cancellation, ABI/API, serialization,
or target condition without an authorized contract change.

| Trap | Typical false optimization | Required check |
| --- | --- | --- |
| Signed overflow | A faster arithmetic rewrite invokes undefined behavior. | Use checked/range proof or unsigned/wider arithmetic while preserving API behavior. |
| `restrict` misuse | Pointers actually alias in a supported call. | Establish and document/enforce non-aliasing at every call boundary. |
| Lifetime/`realloc` | Cached pointer survives reallocation or owner destruction. | Recompute pointers and verify ownership/cleanup paths. |
| Vector tail | SIMD path skips remainder, alignment, or unsupported CPU. | Test all lengths/alignments and retain dispatch/fallback. |
| Error/errno loss | Optimization changes partial-write/error propagation. | Preserve exact return, errno, and cleanup contract. |

Also test the following domain partitions:

- integer width, signed overflow and conversion.
- object bounds, alignment, pointer provenance/lifetime, strict aliasing and
  effective type.
- allocation ownership, realloc invalidation, cleanup and error paths.
- volatile versus atomics, memory order, data races and signal safety.
- locale, errno, floating-point environment, I/O buffering and ABI layout.

Use sanitizers, race tools, Miri, type checkers, or static analyzers only for
the properties they can establish. Their success is not a substitute for runtime
contract tests or matched performance measurement.
