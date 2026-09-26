# Evidence note: does tail sampling cut trace storage by at least 50%?

Claim: tail-based sampling reduces stored trace volume by at least 50% at
equal error-trace recall, for the paper's microservice benchmark only.
Search: OpenAlex, query "tail-based sampling distributed tracing", run
2026-09-25, filter from_publication_date:2020-01-01; arXiv not searched.
Source: Example Study of Tail Sampling; A. Author, B. Author; 2024-03-01;
arXiv:2403.01234v2
Updates: Crossref filter=updates lookup on 2026-09-25: no notices.
Status: full text
Evidence: Table 3 reports 62% lower storage at equal recall (n = 5 runs);
Section 6 notes a single benchmark and no production traffic.
Stats: t(8) = 4.10, p = .003 -> check_stats.py: ok (computed p = 0.0034).
Conclusion: supported, for the benchmark setting only.
