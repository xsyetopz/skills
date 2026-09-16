# Worked investigation: trailing empty field disappears

Synthetic example. Contract: splitting `"a:"` on `":"` produces two fields,
`["a", ""]`. The service instead reports one field after a runtime migration.

Observation: the raw bytes and delimiter are unchanged. The new code uses an API
whose default split behavior drops trailing empty fields. Hypothesis: this API
default, not UTF-8 decoding or the downstream serializer, removes the field.

Experiment: call the split boundary directly with `"a:"`, `":"`, `"a::b"` and
`""`; inspect field count and content before serialization. Repeat with the
API's explicit trailing-empty-preservation control. The discriminating result is
that preservation restores the terminal field while decoding stays unchanged.

Fix the split call's contract, not the serializer. Add expected-value tests for
terminal, leading, adjacent and empty fields; include the consumer integration
that originally counted fields. A test using the same split implementation to
compute expected fields would be circular.

Claim only the observed API-default mismatch. Do not attribute the defect to
“Java being inconsistent” or infer that every parser in the repository is
broken.
