# Diagnose software-development subagent coordination failures

| Symptom | Likely process defect | Corrective action |
| --- | --- | --- |
| Many workers implement incompatible interfaces | Design baseline is underspecified or workers received inconsistent versions | Stop affected work, repair/freeze one interface contract, cancel stale workers |
| Workers repeatedly stub failing functions | Work-item success condition rewards compilation rather than behavior | Tighten item constraints and reviewer rejection criteria; regenerate affected work |
| A review claims success without relevant checks or evidence | Review assignment or evidence may be inadequate | Inspect the actual review scope and evidence; a well-supported clean review is valid and needs no invented defect quota |
| Same defect appears in many work partitions | Shared source-to-target software translation/design rule is wrong | Fix the upstream rule through change control; rerun affected work partitions |
| Parallel workers overwrite changes | Ownership/workspace plan is invalid | Reduce concurrency, assign disjoint writes, or isolate worktrees |
| Huge compiler/test log overwhelms one worker | Queue is not partitioned | Capture once, group by ownership/root cause, assign bounded clusters |
| Build/test commands dominate worker time | Expensive commands are repeated per worker | Run at integration checkpoints; give workers narrower local checks when sound |
| Tests pass after expectations change without contract evidence | The check may have been weakened to match the implementation | Compare with the authoritative contract, repair the test or implementation as evidence requires, and separate verification from repair authority |
| Long comments justify suspicious code | Reviewer accepts workaround narratives over contracts | Require contract/evidence; reject workaround if design does not authorize it |
| Late system test exposes requirement ambiguity | Requirements phase completion check missed observable acceptance behavior | Reopen requirements via change control and invalidate dependent evidence |

The correction target is the **decision rule or shared instruction** that
generated the pattern, not only the latest artifact.
