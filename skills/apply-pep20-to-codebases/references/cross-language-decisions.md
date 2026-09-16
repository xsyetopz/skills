# Apply the principles using the target language

Inspect real consumers, invariants, and tool configuration before choosing a
refactor. The table supplies decision checks, not mandatory rewrites.

| Principle applied | Concrete check | Counterexample to a mechanical rule |
| --- | --- | --- |
| Explicit behavior | Inputs, side effects, error and completion states are distinguishable | A wrapper that silently drops native options is not explicit |
| Readability | A maintainer can trace the required operation and failure path | Short nested expressions can hide order or evaluation timing |
| Sufficient simplicity | Each layer or state has an evidenced responsibility | Removing a justified isolation boundary makes the system simpler only on paper |
| Practical exceptions | A specialized path has a supported target and testable contract | Speculative version branches add obligations the user never required |
| Visible errors | Handling is attached to the operation that owns the failure | Catching lookup and processing together can mislabel an internal failure |
| Refuse material guesses | Resolve an external contract from sources or a user decision | Guessing a timeout, public alias, or production-readiness claim is not implementation discretion |
| One canonical path | Configuration, dispatch, and truth have identified ownership | Multiple necessary targets are not duplicate mechanisms merely because APIs differ |
| Explainability | An unusual implementation has a concrete invariant and evidence | Long comments defending missing behavior do not make it correct |

## Language-specific mechanisms, not Python syntax

- **C:** express buffer lengths and ownership in the interface, check required
  size arithmetic, preserve error codes, and release owned resources on all
  relevant exits. Do not add a C++ abstraction or an unchecked sentinel scheme.
- **C++ and Rust:** use their native lifetime and resource mechanisms;
  distinguish owning from borrowed data. Do not flatten necessary types or
  introduce unsafe operations to make a function shorter. Reallocation and
  concurrent mutation can invalidate assumptions even when a nearby comment
  claims safety.
- **C# and Java:** preserve exception/cancellation semantics and scoped cleanup.
  Do not substitute a default value for an error or turn asynchronous work into
  blocking calls to simplify syntax.
- **JavaScript and TypeScript:** distinguish missing values from legitimate
  falsey values, promise creation from completion, and a static type from
  runtime input validation. Keep required host options and rejection behavior.
- **Go:** preserve error returns, deferred cleanup, goroutine termination, and
  cancellation propagation. A channel or interface needs an actual
  responsibility.
- **Python:** distinguish `None` or missing keys from valid falsey values; scope
  exception translation to the failing operation and own file lifetimes.
- **Firmware and HDL:** express units, widths, ownership of registers, reset and
  clock semantics, and observable effects using the target's native mechanisms.
  Simulation and source clarity do not establish physical timing or electrical
  conformance.

These checks do not authorize adding every named mechanism. Use only the
applicable decision, verify it with the target's existing tools, and preserve
supported behavior. A valid alternative implementation need not resemble the
example or the model's preferred pattern.

Source: [PEP 20](https://peps.python.org/pep-0020/). Cross-language application
and these naming/engineering checks are this collection's requested policy.
