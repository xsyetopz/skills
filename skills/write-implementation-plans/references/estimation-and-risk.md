# Estimate software work and record evidenced delivery risks

Start from the deliverable and its acceptance conditions. Record the source,
date, scope, environment, and completion definition of any historical analogy.
Normalize meaningful differences such as integration count or migration volume;
do not transplant another team's velocity or convert story points into hours.

For decomposition, include design uncertainty, implementation, review,
integration, validation, release work, and rework supported by the context.
Avoid double-counting the same risk in every task and again as global reserve.
Use ranges tied to explicit scenarios; a low/high pair is not a statistical
confidence interval without a model and data supporting that interpretation.

Effort consumes capacity; elapsed time also includes waiting and dependencies.
Model the longest dependent path and resource contention before summing or
parallelizing estimates. Avoid treating all engineers as interchangeable or 100%
available. Use actual availability when known; otherwise make the capacity
assumption explicit and keep dates provisional.

Example: an adapter resembles two previous integrations, but the provider has
not supplied a sandbox. Use the previous work only for the comparable adapter
effort. Keep sandbox waiting time unresolved and put a contract-fixture check
before dependent end-to-end work. Do not invent a delivery date by assuming
immediate access. If a user supplies a fixed date, show which scope is feasible
under the stated access scenarios rather than silently removing validation.

For risk, state “if condition, then consequence,” with evidence for likelihood
and impact. Use qualitative ranges when numerical evidence is absent. A
mitigation reduces exposure; a contingency responds if the risk occurs. Identify
the trigger, owner if known, and capacity/cost implication of each response. An
issue has already happened and belongs in the current dependency picture.

Example: an undocumented import format risks data loss. Mitigate with a bounded
sample audit and restore rehearsal before migration. If the sample exposes
unmapped fields, trigger a scope decision or defer migration; a blanket 20%
buffer does not resolve the missing semantics.

Compare actual completed work and observed blockers with the basis at each
meaningful milestone. Update remaining estimates and assumptions; keep changes
to scope distinct from estimation error. Do not improve apparent predictability
by redefining completion or discarding failed work from the record.

The [GAO estimation guide][gao] supports explicit baselines, assumptions,
sensitivity/risk analysis, and updates from actuals. Apply those principles
proportionately; it does not require a new calculator, parametric model, or
government reporting system for a small software change.

[gao]: https://www.gao.gov/products/gao-20-195g
