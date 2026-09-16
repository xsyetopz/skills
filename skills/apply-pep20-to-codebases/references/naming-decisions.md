# Name the operation and domain object

These are applications of PEP 20's readability and explicitness principles, not
a naming grammar stated by the PEP. Preserve a project's accurate existing
terminology and the target language's native casing and identifier conventions.

## Decide from the contract

1. Identify what a caller supplies, what changes, and what is returned. Use a
   command verb for an operation, a domain noun for data, and the established
   predicate form for a Boolean. Distinguish inspecting, requesting, committing,
   cancelling, and observing completion; these are not equivalent operations.
1. Include the object that disambiguates the action. `write_implementation_plan`
   describes producing a plan; `plan_implementation` can also read as a noun
   compound. `request_cancel` does not claim that work has already stopped.
1. Include units or ownership only where their absence changes interpretation:
   `timeout_ms`, `byte_offset`, `borrowed_stream`, or a native type that carries
   the distinction. Do not repeat type or domain information already clear in
   the surrounding namespace without a reason.
1. Read a proposed name alongside actual call sites and errors. A concise name
   plus a precise contract is preferable to a sentence-length identifier. Add
   contract detail about errors, lifetime, and concurrency where used; do not
   encode the entire algorithm in the name.
1. Inspect references, generated bindings, serialization, configuration, and
   declared public contracts before renaming. Change producer and consumer
   together only within authorized scope. Do not add an old-name alias merely
   because a model assumes all renames require compatibility.

## Distinguishing examples

| Unclear operation | More specific contract |
| --- | --- |
| `process` | Parse a frame, validate its checksum, or publish it: choose the actual operation |
| `cancel` | Request cancellation versus await termination: expose the actual state transition |
| `value` | A temperature, byte count, identifier, or sample interval: name the domain quantity |
| `safe_write` | State atomic replacement, permissions, and durability separately; do not promise unspecified safety |
| `get_or_default` | Define which missing states select a default; zero and empty need not be missing |

Do not rename native API functions, protocol fields, or accepted project terms
just because they could be ambiguous in ordinary English. Explain the relevant
meaning at the boundary. Check the names independently from whether the current
implementation satisfies them.

Source: [PEP 20](https://peps.python.org/pep-0020/).
