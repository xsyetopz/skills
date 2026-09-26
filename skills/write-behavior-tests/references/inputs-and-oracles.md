# Inputs and oracles

How to choose the boundary a test observes, which inputs to use, and
where the expected result comes from. The input techniques follow the
[ISTQB CTFL 4.0.1 syllabus][istqb], chapter 4. Examples are in
[`test_oracles.py`][oracles], and `run_matrix.py` executes them.

## Contents

- Test boundary selection
- Independent expected result
- Equivalence classes and boundary values
- Decision table
- State transition coverage
- Standard vectors, not round trips
- Golden output with narrow normalization

## Test boundary selection

**Definition.** The layer at which a test observes behavior:

- **Unit/component:** a rule over controlled inputs.
- **Integration:** a real database, file system, network stack, or host
  API.
- **Contract:** a producer and a consumer agree on a format.
- **End to end:** the packaged program, driven by a user operation.
- **Install/package:** the built artifact, used outside the checkout.

Pick the smallest layer that can observe the claim ([Just Say No to
More End-to-End Tests][e2e]).

**Use when.** Before writing any test. Map each changed behavior to the
layer that can observe it.

**Do not use when.** Applying a fixed ratio of test types, such as a
pyramid quota, to every repository. Choose per claim instead.

**Example.**

| Claim | Smallest observing layer | Card |
| --- | --- | --- |
| Case-insensitive unique emails | Integration (SQLite) | [real engine][engine] |
| `greetings.json` ships in the wheel | Install/package | [package][package] |
| Percentage bounds | Unit | [boundaries](#equivalence-classes-and-boundary-values) |
| Extension activates in the editor | Host (see the editor skills) | [host][host] |

The first row, observed at the integration layer with a real SQLite
engine, from `assets/examples/behavior/test_doubles.py`:

```python
class UsersTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.addCleanup(self.db.close)

    def test_email_differing_only_in_case_is_rejected(self):
        users = impl.Users(self.db)
        users.add("Ada@example.invalid")

        with self.assertRaises(sqlite3.IntegrityError):
            users.add("ada@example.invalid")
```

**Cost removed.** Slow suites that test rules end to end, and unit
tests that claim host or package behavior they cannot see. In the
package example, the unit test passes from the checkout while the
installed wheel fails.

**Verify.**

1. The report has a claim-to-layer table like the one above.
1. Each claim marked verified has a test at that layer, and the test
   ran.

## Independent expected result

**Definition.** The expected value comes from a source other than the
code under test: a requirement, a standard, a reviewed fixture, or a
separate reference implementation. Never compute it with the same
formula, and never record the current output as the answer.

**Use when.** Every assertion on a computed value.

**Do not use when.** The property is a relation rather than a value,
such as an inverse, monotonicity, or a count. Use a
[property](generative-and-mutation.md#property-based-test) instead.

**Example.**

```python
def test_total_matches_reviewed_value(self):
    # Reviewed requirement: 2 x 199 cents less a 49-cent discount.
    self.assertEqual(impl.invoice_total(199, 2, 49), 349)
```

**Cost removed.** Mistakes shared by the code and the test.
`bug_invoice_no_discount` returns 398 and fails this test. An expected
value recorded from that build, or computed as `price * quantity`,
would pass on the bug. `alt_invoice_addition`, a different algorithm,
passes, so the test does not depend on how the total is computed.

**Verify.**

1. Each expected value names its source in a comment or in the test
   name.
1. A mutant that changes the value fails the test, and a conforming
   alternative passes it (`run_matrix.py --only invoice`).

## Equivalence classes and boundary values

**Definition.** Split the input into classes that the contract treats
alike (equivalence partitioning). Test one representative per class and
each boundary with its neighbors. For an inclusive integer range
1 to 100, test 0, 1, 2, 99, 100, and 101. Missing or malformed input
is its own class.

**Use when.** The input is ordered or partitioned: ranges, lengths,
sizes, dates, versions.

**Do not use when.** The input has no order, such as enum members. Use
a [decision table](#decision-table) or one test per member instead.

**Example.**

```python
def test_boundaries_and_neighbors(self):
    expected = {0: False, 1: True, 2: True, 99: True, 100: True, 101: False}
    for value, accepted in expected.items():
        with self.subTest(value=value):
            self.assertIs(impl.accept_percentage(value), accepted)
```

**Cost removed.** Off-by-one errors. `bug_percentage_off_by_one`
(`1 <= value < 100`) fails this test at `value=100` but passes
`WeakPercentage`, which tests only 50 and 150. `mutate.py` on
`accept_percentage` kills all 5 mutants with this suite; with a
middle-only suite, the boundary mutants survive (`test_mutate.py`).

**Verify.**

1. Each boundary in the contract appears with both neighbors.
1. `mutate.py --function <name>` reports no surviving `compare` or
   `constant` mutant.

## Decision table

**Definition.** When conditions interact, list every feasible
combination with its expected action, and test each row.

**Use when.** The outcome depends on two or more inputs together, such
as role and account state, or a feature flag and a plan.

**Do not use when.** The conditions are independent. Test each one
alone; the product of combinations adds nothing.

**Example.**

```python
TABLE = {
    ("admin", "active"): True,
    ("admin", "suspended"): True,
    ("editor", "active"): True,
    ("editor", "suspended"): False,
    ("viewer", "active"): False,
    ("viewer", "suspended"): False,
}
```

**Cost removed.** Missed combinations. `bug_can_edit_suspended`, which
lets editors edit suspended accounts, passes `WeakPermissions` (one
flag at a time) and fails the table test at `("editor", "suspended")`.

**Verify.**

1. The table has one row for every combination, or the report names
   the rows that are infeasible.
1. `run_matrix.py --only can_edit` shows the table test failing and the
   weak test passing.

## State transition coverage

**Definition.** For stateful behavior, test every allowed transition,
and test that every other (state, event) pair is rejected. Visiting
every state once does not cover the transitions between them.

**Use when.** The code has states and events, such as a workflow, a
protocol, or a connection.

**Do not use when.** The state space is too large to list. Use a
[stateful property test](generative-and-mutation.md#stateful-model-test)
against a model instead.

**Example.**

```python
def test_every_other_pair_is_rejected(self):
    for state in STATES:
        for event in EVENTS:
            if (state, event) in ALLOWED:
                continue
            with (
                self.subTest(state=state, event=event),
                self.assertRaises(ValueError),
            ):
                impl.next_state(state, event)
```

**Cost removed.** Illegal shortcuts. `bug_state_skip_review` allows
`draft + approve -> published`. It passes the happy-path test that
visits every state, and fails the forbidden-pairs test at
`state='draft', event='approve'`.

**Verify.**

1. Count the pairs: allowed plus rejected equals states times events
   (here 4 plus 12 equals 16).

## Standard vectors, not round trips

**Definition.** For an encoder, parser, or serializer, compare against
test vectors from the standard, not only `decode(encode(x)) == x`,
which passes whenever both sides share the same mistake.

**Use when.** The format has a specification: RFC 4648 for base64,
RFC 8259 for JSON, SemVer, protocol messages.

**Do not use when.** The format is private to one program and both
sides always change together. Then the round trip is the contract.

**Example.**

```python
# RFC 4648 section 10, plus 0xfbff which uses alphabet values 62 ('+')
# and 63 ('/') from Table 1.
VECTORS = {
    b"": "",
    b"f": "Zg==",
    b"foobar": "Zm9vYmFy",
    b"\xfb\xff": "+/8=",
}
```

The RFC 4648 section 10 vectors contain no `+` or `/`. The added vector
covers the last two alphabet entries.

**Cost removed.** Wrong-format output that the program's own decoder
accepts. `bug_b64_urlsafe` emits `-_8=`, passes
`WeakBase64.test_round_trip`, and fails `test_standard_vectors`.

**Verify.**

1. Each vector cites its section of the standard.
1. At least one vector covers each character class of the format.

## Golden output with narrow normalization

**Definition.** A golden (snapshot) test compares the full output with
a reviewed expected text. Normalize only volatile fields, such as
timestamps or random ids. Never normalize order, content, or errors.

**Use when.** The output is intentionally stable: a report, a
generated file, CLI help, a rendered template.

**Do not use when.** Most of the output is incidental formatting.
Assert the specific fields instead. Never update a golden file without
reviewing the diff.

**Example.**

```python
def test_report_matches_reviewed_golden_text(self):
    text = impl.render_report([("beta", 1), ("alpha", 3)], "2026-09-25T10:00Z")
    normalized = text.replace("2026-09-25T10:00Z", "<TIME>", 1)
    self.assertEqual(normalized, GOLDEN)
```

**Cost removed.** Order and content regressions that a broad
normalization hides. `bug_report_unsorted` passes `WeakSnapshot`,
which sorts the lines before comparing, and fails the golden test.

**Verify.**

1. The normalization replaces only named fields, and the test shows
   which ones.
1. Any golden update in the diff has a reviewer note for each changed
   line.

[istqb]: https://istqb.org/wp-content/uploads/2024/11/ISTQB_CTFL_Syllabus_v4.0.1.pdf
[oracles]: ../assets/examples/behavior/test_oracles.py
[e2e]: https://testing.googleblog.com/2015/04/just-say-no-to-more-end-to-end-tests.html
[engine]: coupling-and-doubles.md#real-engine-for-engine-semantics
[package]: boundaries-and-hardware.md#installed-package-test
[host]: boundaries-and-hardware.md#host-dependent-behavior
