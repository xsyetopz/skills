# Write precise task language for AI Agent Skills

Use a concise action and specific object, or an established domain capability
name. Read the name together with its activation description: the name
identifies the task, and the description supplies its trigger and nearest
exclusions. Do not force the entire procedure or every possible meaning into the
identifier. Correct wording is an input to evaluation, not a guarantee that an
agent cannot misinterpret it.

## Write names and activation descriptions

1. Start the directory/name with an action: implement, configure, inspect,
   measure, test, review, migrate, or another verb matching the actual result.
   Include the technical object or domain. Keep the standard 64-character limit
   and directory/frontmatter identity; do not add numeric ordering prefixes.
1. Check grammar as well as length. `write-implementation-plans` describes an
   action and artifact; `plan-implementation` can read as a noun compound. Keep
   approved accurate names; do not churn names to save a character.
1. State the specialized operation and its intended input in the description.
   Distinguish creating, reviewing, executing, measuring, publishing, and
   deleting. A request for one does not authorize the others.
1. Give methodology or product names their technical context. Use “Waterfall
   software development model,” “Bun JavaScript toolchain,” “Zed code editor,”
   or “Rust programming language” where an unqualified name could mislead. Do
   not replace the product's actual name with a made-up synonym.
1. Exclude the nearest plausible different task, not a long list of unrelated
   meanings. Describe the supported operation rather than filling metadata with
   distracting words such as tourism or cooking to deny those domains.
1. Keep native API names, filenames, CLI options, event names, and code symbols
   exact. Explain their meaning instead of renaming the underlying mechanism.
   For example, IntelliJ Platform dumb mode is index-unavailable operation; a
   Git index is the staged snapshot, not a search index.

| Ambiguous wording | State the operation and domain |
| --- | --- |
| Waterfall delivery | Complete sequential software-development phases and their required checks |
| Run the gate | Execute the named checks; advance only when the recorded criteria pass |
| Use an oracle | Evaluate the independent expected-result rule named for this test |
| Shard the work | Assign independent software tasks with explicit write paths and prerequisites |
| Port this | Translate named source-language constructs or adapt the named platform integration |
| Fix the host | Identify whether the target is the agent client, editor process, operating system, or remote service |
| It is green | State which build or test command passed on which revision |
| Apply Zen | Apply PEP 20 to the specified codebase's design or naming in its own language |

## Apply terminology throughout the package

Define a term before relying on it to control an operation. A phase baseline,
performance baseline, and old executable used for comparison are different
objects. Name the exact version, result, or record whenever that distinction
affects the task.

Use the same term for the same object throughout the entry point, conditional
references, template labels, script help, and Codex UI metadata. References that
can be read independently need a domain-specific title and enough local context
to interpret the instructions. Do not require a catalog-wide glossary.

Replace vague commands with executable decisions: which input or path to read,
which condition to check, what to do on each outcome, what may change, and what
must remain unchanged. “Review adversarially” is not a procedure. Specify an
independent software reviewer, the contracts to inspect, evidence required for a
finding, and the prohibition on editing implementation during review.

For template fields, identify the expected object and units. For script options,
retain existing native flags and compatibility while making help text precise.
Do not change functional code, provider controls, or test expectations merely to
make terminology uniform.

## Evaluate interpretation separately from formatting

Review metadata without the body: can a reader identify the operation, domain,
input, and nearest exclusion? Then exercise actual target-client selection with
real requests, near misses, short descriptions, alternative wording, and
composite tasks. Keep both selection and non-selection cases; unrelated words
alone should not trigger a skill.

For instructions, check observable behavior: selected files, commands, scopes,
phase order, result classification, and preserved native options. A valid
schema, a keyword checker, or a name-length check cannot establish semantic
understanding. Record authored test cases separately from executed agent trials.
Use [description evaluation](description-evaluation.md) for actual experiments.

Sources: [Agent Skills descriptions][descriptions], [creator
guidance][guidance].

[descriptions]: https://agentskills.io/skill-creation/optimizing-descriptions
[guidance]: https://agentskills.io/skill-creation/best-practices
