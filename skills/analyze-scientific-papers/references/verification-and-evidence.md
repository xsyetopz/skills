# Verification and evidence

Select evidence at the boundary of the claim. Run the smallest sufficient set
first, then broaden only when the change crosses another contract boundary.

| Claim | Sufficient evidence | Not sufficient by itself |
| --- | --- | --- |
| A paper reports a specific effect | Exact result table/text, estimate, scale, uncertainty, population, and analysis set. | Title, abstract snippet, or review summary alone. |
| A method supports a causal claim | Design and analysis that identify the causal contrast, with assumptions and limitations. | Temporal order or author language alone. |
| A result replicated | Independent study using a sufficiently comparable construct and analysis, or a defined replication study. | A citation, conceptual similarity, or repeated claim. |
| The evidence base is comprehensive | Documented databases, queries, dates, screening, de-duplication, and follow-up searches appropriate to the question. | One search engine page. |
| A paper is current and valid | Version, correction/retraction status, and authoritative record checked. | An old local PDF filename. |

## Command patterns

```sh
python scripts/fetch_metadata.py --help
python -m unittest scripts.test_fetch_metadata
```

The helper retrieves provider-native metadata for discovery. It does not read
papers or grade evidence.

## Result reporting

Separate authored checks, executed checks, static analysis, simulation,
integration/host execution, production observations, skipped checks, and
unavailable checks. Include relevant failure output. A green check establishes
only the properties it can discriminate; a single flaky pass, successful parser,
or valid configuration file is not broad runtime proof.
