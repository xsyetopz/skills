# Claim-to-source verification for Scientific Literature

Select evidence that can discriminate the claimed property of the paper
synthesis. Run the smallest sufficient check first. Broaden only when another
contract boundary changed.

| Claim | Sufficient evidence | Not sufficient by itself |
| --- | --- | --- |
| A paper reports a specific effect | Exact result table/text, estimate, scale, uncertainty, population, and analysis set. | Title, abstract snippet, or review summary alone. |
| A method supports a causal claim | Design and analysis that identify the causal contrast, with assumptions and limitations. | Temporal order or author language alone. |
| A result replicated | Independent study using a sufficiently comparable construct and analysis, or a defined replication study. | A citation, conceptual similarity, or repeated claim. |
| The evidence base is comprehensive | Documented databases, queries, dates, screening, de-duplication, and follow-up searches appropriate to the question. | One search engine page. |
| A paper is current and valid | Version, correction/retraction status, and authoritative record checked. | An old local PDF filename. |

## Command patterns

```sh
python3 scripts/fetch_metadata.py --help
python3 -m unittest scripts.test_fetch_metadata
```

The helper retrieves provider-native metadata for discovery. It does not read
papers or grade evidence.

## Result reporting

For the paper synthesis, separate authored checks, executed checks, static
analysis, simulation, host/integration execution, production observations,
skips, and unavailable checks. Include useful failure output. A green check
establishes only the property that it can discriminate.
