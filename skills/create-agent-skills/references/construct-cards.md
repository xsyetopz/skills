# Construct cards

A construct card leaves an agent no room to invent: one construct (API,
language feature, pattern, technique, command, file format, or decision)
with its definition, applicability, a working example, the cost it
removes, and the steps that prove it worked. The template is
[`assets/card.template.md`](../assets/card.template.md).

## Contents

- Card structure
- Choosing constructs
- Variants
- Examples that run
- Cost removed and measurement
- Verification tiers
- Grounding and numbers
- Non-code skills

## Card structure

**Definition.** Six parts, in order:

1. **Definition**: one or two precise sentences on what it is and what it
   does mechanically.
1. **Use when**: concrete, checkable conditions (observable in code, a
   profile, or the request).
1. **Do not use when**: concrete conditions and the failure that results.
1. **Example**: complete, self-contained, working code or artifact in the
   target language (at most 80 columns per line in Markdown), with a pointer
   to the runnable file.
1. **Cost removed**: the exact cost removed or reduced and how to observe
   it (tool, metric, expected direction).
1. **Verify**: exact commands that prove behavior was preserved and that
   the claimed benefit appeared.

**Use when.** Any construct an agent might apply, choose between, or be
tempted to invent.

**Do not use when.** Background facts that support several cards (a
tool's version history, a glossary) go in the card that uses them or in
a short introduction.

**Example.** A complete card, from `optimize-csharp-code`:

````markdown
### IEquatable on struct keys

**Definition.** `Dictionary<TKey,TValue>` and `EqualityComparer<T>.Default`
call `IEquatable<T>.Equals(T)` when the struct implements it; otherwise
they fall back to `ValueType.Equals(object)`, which boxes the key.

**Use when.**

- A struct is a dictionary/set key or is compared in hot code.

**Do not use when.**

- `Equals(object)`, `GetHashCode`, and `Equals(T)` would disagree; lookups
  then miss silently.

**Example.**

```csharp
public readonly struct EquatableKey(int a, int b)
    : IEquatable<EquatableKey>
{
    public int A { get; } = a;
    public int B { get; } = b;
    public bool Equals(EquatableKey other) =>
        A == other.A && B == other.B;
    public override bool Equals(object? obj) =>
        obj is EquatableKey other && Equals(other);
    public override int GetHashCode() => HashCode.Combine(A, B);
}
```

**Cost removed.** Boxing per lookup. Local: 72 B/op and 21.3 ns versus
0 B/op and 2.8 ns (M1 Max, .NET 10.0.11, BenchmarkDotNet short job).

**Verify.**

1. `sh assets/examples/verify.sh verify` compares lookups on both keys.
1. `Check.NoAllocation("iequatable-key", ...)` passes.
````

**Cost removed.** Agents filling gaps from memory: wrong API names,
missing preconditions, unmeasured claims.

**Verify.**

1. Each `###`/`##` card heading in the reference is followed by all six
   bold labels. Review by reading, not with a density script.

## Choosing constructs

**Definition.** The constructs an expert would check or consider for
this task, drawn from real tasks, official documentation, and observed
agent failures, not from a topic outline.

**Use when.** Starting or auditing a skill.

**Do not use when.** The base model already applies the construct
correctly and no failure shows otherwise. Anthropic's default assumption
is that the model is capable; add only what it lacks
([best practices][anthropic-bp]).

**Example.** Sources for the C# list: the runtime's "what's new" pages,
BenchmarkDotNet guides, known semantic traps (`HasFlag` any-versus-all), and
things agents did wrong (claiming "zero allocation" from tier-0 runs).

**Cost removed.** Cards nobody needs, and missing cards for the
decisions agents actually get wrong.

**Verify.**

1. Every eval prompt maps to at least one card, and the SKILL.md routing
   table reaches every card.

## Variants

**Definition.** A construct with a different mechanism, precondition,
or verification, such as `stackalloc` with an `ArrayPool` fallback
versus `ArrayPool` alone. Each variant gets its own card.

**Use when.** Two forms differ in when they are safe or how they are
checked.

**Do not use when.** The difference is only syntax (a method call versus
extension syntax); mention it inside one card.

**Example.** `CollectionsMarshal.AsSpan` and
`CollectionsMarshal.GetValueRefOrAddDefault` are separate cards: they
differ in data structure and invalidation rules.

**Cost removed.** A variant's precondition hidden inside another card.

**Verify.**

1. Each card has exactly one "Definition" and its own Verify steps.

## Examples that run

**Definition.** Example code is a complete method, type, or file that
compiles as shown, taken from (or identical to) a runnable asset that the
skill's verifier builds and executes.

**Use when.** Always for code; for artifacts, see "Non-code skills".

**Do not use when.** Never publish pseudo-code (`...`, `// handle error`)
as a construct's example; an agent will copy it.

**Example.** In references: an 80-column excerpt plus "Runnable:
`assets/examples/constructs/Allocation.cs`". In assets: baseline and
candidate implementations, an oracle comparing them on edge cases, and an
assertion of the claimed benefit (for example
`Check.NoAllocation("span-parsing", ...)`).

**Cost removed.** Examples that do not compile or that silently change
behavior.

**Verify.**

1. The skill's `verify.sh` (or test runner) builds and runs every example
   in a disposable copy and exits non-zero on any mismatch.

## Cost removed and measurement

**Definition.** The card states which cost falls (allocations, calls,
round trips, lock contention, startup JIT work, ambiguity, rework) and
the instrument that shows it: a benchmark column, a counter, a profiler
frame, a compiler diagnostic, a lint rule, or a script's count.

**Use when.** Every card. For semantic-safety cards (for example,
"`HasFlag` means all bits"), the cost is the bug prevented and the
instrument is the oracle.

**Do not use when.** The only evidence is intuition. If the benefit could
not be measured, say so and label the card as preventing a failure, not
improving a metric.

**Example.** "Local oracle output: `ALLOC valuetask: 72 B -> 0 B`" and
"Local: no measurable difference because dynamic PGO already
devirtualizes the monomorphic call." Both are valuable; the second stops
an agent from making a useless change.

**Cost removed.** Changes kept on faith.

**Verify.**

1. Each numeric claim names its source: a linked document, or a local run
   with command, machine, and toolchain.

## Verification tiers

**Definition.** Each example set states how far it was checked:

- **Executed**: ran in the author's session, output recorded.
- **Compiled**: built or type-checked, not run (with the reason).
- **Not runnable here**: host, SDK, or hardware unavailable; the exact
  command is given and marked unexecuted.

**Use when.** Every runnable asset, and every card whose Verify step the
author could not run.

**Do not use when.** Never label an unexecuted command as passing.

**Example.** "Native AOT: not runnable here. The Homebrew .NET SDK 10.0.400
failed the native link step (`MSB3073`); the commands are the documented
flow and are unexecuted locally."

**Cost removed.** Users trusting unverified instructions.

**Verify.**

1. Each example set has "Executed", "Compiled", or "Not runnable" near
   it.

## Grounding and numbers

**Definition.** Every API name, flag, config key, default, version
boundary, and behavior claim cites a primary source (official docs,
language standard, runtime repository, tool manual). Numbers come only
from a cited source or a labeled local measurement.

**Use when.** Always.

**Do not use when.** The only source is a secondary summary (blog,
generated answer, search snippet); confirm against the primary page or
mark the claim unverified.

**Example.** "DATAS is enabled by default starting in .NET 9
([GC config][gc-config])" versus the invented "DATAS reduces memory by
40%".

**Cost removed.** Confident, wrong instructions.

**Verify.**

1. Every external link resolves (for example, `curl -sIL` on each URL),
   and the cited sentence supports the claim.
1. Every number with a unit has a source or a local-run label:
   `rg -n '[0-9]+(\.[0-9]+)? ?(ns|ms|%|x)\b'`.

## Non-code skills

**Definition.** For skills whose output is a document or an operation
(requirements, plans, reviews, changelogs, Git hosting), the example is
the complete artifact in its native form (an EARS requirement set, a
plan table, a changelog entry, a CLI session with real flags). The
measurable cost is a count from a script or command (requirements
without an acceptance test, plan steps without a verification command).

**Use when.** The skill produces text artifacts or remote operations.

**Do not use when.** Never invent percentages ("reduces rework by 30%");
a checker's counts are the measurement.

**Example.** A requirements skill ships a stdlib checker that parses EARS
statements and exits 1 when a requirement lacks an ID or an acceptance
criterion. The card's Cost removed is "requirements without acceptance
criteria: N → 0 as reported by the checker".

**Cost removed.** Unverifiable prose instructions.

**Verify.**

1. The checker has tests and runs in the skill's verify step.

[gc-config]: https://learn.microsoft.com/en-us/dotnet/core/runtime-config/garbage-collector
[anthropic-bp]: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
