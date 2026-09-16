# Worked examples for scientific-paper analysis

## Example 1: one paper, one disputed claim

**Question:** Does the named paper show that treatment X reduces outcome Y in
the entire target population?

1. Resolve the DOI and check for corrections, retractions, protocol, and
   supplement.
1. Read eligibility criteria and the analysis population. Record exclusions and
   missing-data handling.
1. Extract the treatment contrast, endpoint definition, follow-up interval,
   effect estimate, confidence interval, and analysis model.
1. Compare the user’s phrase “entire target population” with the actual sampled
   population and estimand.
1. Answer in two layers: what the paper reports, then whether that supports the
   broader target claim.

A compliant conclusion can be: “The randomized comparison estimates X versus Y
among enrolled participants meeting criteria A–D at 12 weeks. It does not by
itself establish effectiveness in excluded group E or beyond 12 weeks.”

## Example 2: conflicting performance studies

Suppose three papers benchmark a compiler optimization:

| Study | Hardware | Workload | Baseline | Reported result |
| --- | --- | --- | --- | --- |
| A | server CPU | batch throughput | compiler v1 | +18% throughput |
| B | laptop CPU | interactive latency | compiler v2 | no clear change |
| C | GPU target | kernel runtime | hand-tuned code | -7% runtime |

Do not average 18, 0, and 7. First map each study to the requested workload,
version, metric, and target. A useful synthesis explains that A addresses server
throughput, B addresses interactive latency under a different compiler, and C
addresses a different execution target. The correct next action may be a local
matched benchmark rather than a pooled literature number.

## Example 3: metadata is discovery, not evidence

```python
records = fetch_records(query)
for record in records:
    print(record["doi"], record["title"])
```

This can create a candidate set. It cannot establish sample size, model,
outcomes, or limitations unless those fields are opened in the authoritative
paper or registry. Preserve the provider response so de-duplication and later
corrections are auditable.
