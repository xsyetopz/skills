# Behavior models

Structures that expose missing cases before requirements are written:
glossaries, state tables, decision tables, and explicit rules for
concurrency and retries. The worked state table is in
[`export-cancellation-spec.md`](../assets/examples/export-cancellation-spec.md).

## Contents

- Glossary with identity and lifetime
- Units and domains
- State transition table
- Decision table
- Linearization point for races
- Retry and idempotency semantics
- Abuse cases

## Glossary with identity and lifetime

**Definition.** A list of the domain nouns, with what identifies each and
when it exists. "File" can mean a path, an open descriptor, an inode, an
uploaded object, or a published version, each with a different identity.

**Use when.** The request uses nouns with several possible meanings
(file, user, account, session, job).

**Do not use when.** The project already has a glossary; reuse its terms.

**Example.**

```text
- Temporary file: the file a job writes before publication; owned by
  that job only.
- Publication: the atomic rename of the temporary file onto the
  destination.
```

**Cost removed.** Two readers implementing different things under one
name.

**Verify.**

1. Every noun in a requirement is in the glossary or is unambiguous.
   `scripts/term_report.py` from write-readable-code counts competing
   synonyms in the spec.

## Units and domains

**Definition.** State units and value domains explicitly: bytes or
characters, UTC timestamp or local date, inclusive or exclusive bounds,
ordered sequence or set, empty or absent, exact or with tolerance.

**Use when.** Any requirement contains a quantity, time, range, or
collection.

**Do not use when.** A cited external standard fixes the unit; cite it
instead.

**Example.** "Export names are 1 to 255 bytes of UTF-8, inclusive" rather
than "names up to 255 characters".

**Cost removed.** Boundary disputes and unit bugs.

**Verify.**

1. Run `rg -n '\b(characters|chars|size|length|time|date|limit)\b' SPEC.md`
   and confirm each hit has a unit and a bound style.

## State transition table

**Definition.** A table of (current state, event) → (next state, observable
effect), covering every state and every event, including repeats and late
events.

**Use when.** An entity has a lifecycle (jobs, orders, sessions,
connections).

**Do not use when.** The behavior is a stateless input-to-output mapping;
use a decision table.

**Example.**

```text
| State      | Event            | Next state | Observable effect          |
| writing    | cancel accepted  | cancelled  | temp file removed          |
| publishing | cancel requested | publishing | "publication started"      |
| published  | cancel requested | published  | outcome stays published    |
| cancelled  | cancel requested | cancelled  | no new effects             |
```

Every empty (state, event) cell is a question for the user.

**Cost removed.** Unspecified late, repeated, and concurrent events.

**Verify.**

1. Count states × events. Every combination is a row or is listed as
   impossible, with the reason.

## Decision table

**Definition.** A table whose columns are conditions and whose rows list
each combination with the required action: one row per rule, no
overlaps, no gaps.

**Use when.** An outcome depends on three or more independent conditions
(role, plan, feature flag, region).

**Do not use when.** There are only one or two conditions; EARS
statements suffice.

**Example.**

```text
| Owner | Admin | Export published | Cancel allowed |
| yes   | any   | no               | yes            |
| no    | yes   | no               | yes            |
| no    | no    | no               | no (403)       |
| any   | any   | yes              | no (409)       |
```

**Cost removed.** Conflicting or missing permission rules.

**Verify.**

1. The rows cover all 2^n combinations, using "any" explicitly where it
   applies; each row maps to one requirement and one acceptance criterion.

## Linearization point for races

**Definition.** For competing operations, name the single state change
that decides the winner (a lock, a compare-and-set, a database
transaction), not wall-clock arrival.

**Use when.** Two actors can act on the same entity concurrently (cancel
versus publish, two updates).

**Do not use when.** The system is single-threaded with a queue; the
queue order is the linearization.

**Example.** "The change to publishing is the linearization point for
cancellation; a cancel accepted before it wins, one after it reports
publication started."

**Cost removed.** Race outcomes left to chance.

**Verify.**

1. The acceptance tests cover both orders with a barrier (see
   [acceptance](acceptance.md#controlled-interleavings)).

## Retry and idempotency semantics

**Definition.** State what a retry does: whether a second identical
request repeats the business effect, returns the first result, or is
rejected, and how the service recognizes a repeat.

**Use when.** Requests cross a network or a queue with at-least-once
delivery.

**Do not use when.** You would add an idempotency-key protocol the system
does not need. If retries repeat the effect by contract, state that
instead.

**Example.** REQ-EXP-004: "While a job is cancelled or published, the
export service shall treat a repeated cancel request as a no-op that
returns the current outcome."

**Cost removed.** Duplicate side effects under retry.

**Verify.**

1. An acceptance criterion sends the same request twice and asserts the
   second response and the absence of new effects.

## Abuse cases

**Definition.** Scenarios written from an attacker's or misuser's goal
(cancel someone else's export, fill the disk with exports), each turned
into an unwanted-behavior requirement ([OWASP abuse case cheat
sheet][owasp-abuse]).

**Use when.** The feature crosses a trust boundary (user input, multiple
tenants, public endpoints).

**Do not use when.** The threat has no path into the system. Tie each
case to an input the attacker controls.

**Example.** "If a user requests cancellation of a job they do not own,
then the export service shall reject the request without revealing
whether the job exists."

**Cost removed.** Authorization gaps found after release.

**Verify.**

1. Each abuse case has an `If ... then` requirement and a negative
   acceptance test.

[owasp-abuse]: https://cheatsheetseries.owasp.org/cheatsheets/Abuse_Case_Cheat_Sheet.html
