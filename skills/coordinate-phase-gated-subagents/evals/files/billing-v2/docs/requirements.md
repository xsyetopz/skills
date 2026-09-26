# Requirements baseline: billing v2 (frozen)

| ID | Requirement | Verified by |
| --- | --- | --- |
| R1 | Invoice totals include tax per line, rounded half-up to cents. | unit tests |
| R2 | A finalized invoice is emailed to the customer's billing contact. | end-to-end suite on staging |
| R3 | Application logs contain no customer email addresses. | PII log scan |
