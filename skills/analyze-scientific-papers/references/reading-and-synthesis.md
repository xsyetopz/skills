# Reading and synthesis

Turning papers into a conclusion someone can check. Evidence notes follow
`assets/evidence-note-template.md`; `scripts/check_evidence_note.py`
checks them, and `scripts/check_stats.py` checks reported statistics.

## Contents

- Evidence level
- Claim to location
- Statistical consistency check
- Effect size and uncertainty over significance
- Study design appraisal
- Conflicting studies without vote counting
- Applicability to the question

## Evidence level

**Definition.** What was read:

- metadata;
- the abstract;
- the full text;
- the code or data.

Only full text, or code and data, can support or contradict a claim.
Metadata and abstracts can only point to what to read.

**Use when.** Before writing any conclusion.

**Do not use when.** Never use citation counts or search rank as the
evidence level; they measure attention, not correctness.

**Example.** The checker rejects the abstract-only note:

```text
note-abstract-only.md: supported from abstract only: read the full text first
```

**Cost removed.** Conclusions built on abstracts that overstate results.

**Verify.**

1. `check_evidence_note.py NOTE.md` passes for every note behind the
   answer.

## Claim to location

**Definition.** Each supporting statement names its location: a section,
table, figure, or page. It separates what the authors claim from what
their data show.

**Use when.** Every sentence in the answer that asserts a finding.

**Do not use when.** Never paraphrase a whole paper as one claim.

**Example.** "Table 3 reports 62% lower storage at equal recall (n = 5
runs); Section 6 notes a single benchmark."

**Cost removed.** Unverifiable summaries; a reader can open the table and
check it.

**Verify.**

1. The checker's rule "evidence names no section, table, figure, or
   page" passes.

## Statistical consistency check

**Definition.** Recompute the p-value from the reported statistic and
degrees of freedom, and compare it with the reported p, allowing for
rounding. This is the method of statcheck. Its authors found at least
one inconsistent p-value in half of the psychology papers from 1985 to
2013 that used significance tests (Nuijten et al., [2015][statcheck]).

**Use when.** A paper's conclusion rests on reported tests: t, F, χ²,
z, or r.

**Do not use when.** Never read an inconsistency as proof of misconduct.
It may be a typo or a one-tailed test; read the context first.

**Example.** Executed on `assets/examples/results-section.txt`:

```text
ok   't(28) = 2.20, p = .036': computed p = 0.0362 (range 0.0358-0.0366)
FLAG 't(28) = 1.20, p = .03': computed p = 0.2402 (range 0.2383-0.2421)
```

The stdlib implementation matches SciPy 1.16.2 to within 1.6e-13 on a
grid of t, F, and χ² values (the network mode of `verify.sh`).

**Cost removed.** Relying on a significant result that the reported
statistic does not support.

**Verify.**

1. `check_stats.py FILE` output is recorded in the note's `Stats:`
   field.

## Effect size and uncertainty over significance

**Definition.** Report the effect size and its uncertainty: a confidence
interval, the variance across runs, the sample size. Whether p crossed
.05 is not the finding. The ASA statement's fifth
principle: "A p-value, or statistical significance, does not measure
the size of an effect or the importance of a result" ([ASA 2016][asa]).

**Use when.** Summarizing any quantitative result.

**Do not use when.** Never write "significant improvement" without the
effect size and interval.

**Example.** "62% lower storage (n = 5 runs; runs varied 55–70%)",
not "significantly lower storage".

**Cost removed.** Treating tiny effects as meaningful because p < .05.

**Verify.**

1. Each quantitative claim in the answer states the size, the
   uncertainty, and n.

## Study design appraisal

**Definition.** Check the features that decide whether a result is
credible:

- randomization or controlled comparison;
- baselines that are strong and tuned alike;
- sample size;
- preregistration;
- data and code availability;
- whether the evaluation data overlaps the training or tuning data.

**Use when.** Before relying on a result, especially a surprising one.

**Do not use when.** Never let the venue's prestige replace the checks.

**Example.** A benchmark paper that tunes its own method but runs the
baselines at default settings has a comparison that favors the
proposal.

**Cost removed.** Adopting results that do not survive a fair
comparison.

**Verify.**

1. The note's `Evidence:` field lists the design limitations found, or
   says none were found and what was checked.

## Conflicting studies without vote counting

**Definition.** When studies disagree, compare their designs,
populations, measures, and effect sizes. Do not count significant
versus non-significant results. The Cochrane Handbook calls vote
counting based on statistical significance "unacceptable"
([chapter 12][cochrane]).

**Use when.** Two or more studies address the same question with
different results.

**Do not use when.** Never conclude "most studies show X".

**Example.** Two studies report opposite latency effects. One ran on
synthetic load, the other on production traces. The conclusion is
scoped to each setting, and not averaged.

**Cost removed.** Conclusions that reflect how many studies exist, not
what they show.

**Verify.**

1. The synthesis names the design difference that explains each
   disagreement, or states that the disagreement is unexplained.

## Applicability to the question

**Definition.** Map each finding's setting onto the user's setting:
population, scale, versions, hardware, and date. Carry that scope into
the conclusion.

**Use when.** Answering a practical question with research results.

**Do not use when.** Never generalize from one benchmark to production
without saying so.

**Example.** "Supported, for the benchmark setting only." That is the
conclusion in `note-supported.md`.

**Cost removed.** Decisions based on results from a different setting.

**Verify.**

1. Every conclusion carries a scope clause.

[statcheck]: https://doi.org/10.3758/s13428-015-0664-2
[asa]: https://doi.org/10.1080/00031305.2016.1154108
[cochrane]: https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-12
