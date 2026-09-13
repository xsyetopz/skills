---
name: select-development-process
description: >-
  Choose or revise a software development lifecycle and feedback process from
  uncertainty, delivery constraints, and verification needs. Not for estimating
  or scheduling delivery, or imposing ceremonies on ordinary implementation.
---

# Select Development Process

Deliver a justified working process, not a preferred model label. Respect an
explicitly required lifecycle; explain a conflict rather than replacing it.
Use the smallest process that addresses the project's actual risks. Do not
create schedules, mandatory document sets, or approval ceremonies by default.

## Identify the forces

Determine requirement stability and its evidence, technical uncertainty,
stakeholder feedback access, separability of useful releases, integration
constraints, cost of rework, and required verification/acceptance evidence.
Record imposed contractual milestones and safety or assurance obligations only
when supplied or verified. Unknown feedback access is a missing input, not
permission to assume continuous customer participation.

Separate lifecycle structure from methods and practices: iterative refinement
can also deliver increments; agile principles can guide either. Scrum is a
framework, not a synonym for all agile work. CI, reviews, prototyping, and test
automation can support multiple lifecycles. Select compatible mechanisms rather
than treating these labels as mutually exclusive products.

## Compare relevant candidates

| Approach | Favor when | Cost or condition to address |
| --- | --- | --- |
| Sequential / Waterfall | Stable baselines and externally constrained handoffs make phase coordination useful | Late integration is risky; define early feasibility checks and a return path when evidence invalidates a baseline. Stability alone is insufficient. |
| Iterative | The solution needs repeated refinement from evidence | Each cycle needs a question, reviewable result, and exit criterion; repetition without feedback is not learning. |
| Incremental | Useful capability can be delivered in compatible slices | Define integration and data/contract evolution; disconnected components are not usable increments. |
| V-model | Requirements/design levels need explicit corresponding verification and validation evidence | Plan checks alongside their specification levels; do not postpone all testing until implementation or infer a universal document mandate. |
| Spiral | Technical or operational risk should determine the next investment | Each cycle evaluates objectives, alternatives, risk-reduction evidence, and the next commitment; cost must be justified by risk. |
| Prototyping | A concrete experiment can resolve usability, feasibility, or interface uncertainty | Name the question and deciding observation; declare throwaway versus evolutionary intent and what production evidence remains absent. |
| RAD | Timeboxed delivery can reuse components with available users and separable scope | Verify integration, skills, and feedback capacity; rapid construction does not remove quality or migration work. |
| Agile approaches | Frequent feedback and reprioritization can guide working increments | Specify who provides feedback and how changes enter the next slice; ceremonies or short deadlines alone do not provide agility. |

Compare the viable candidates against the same forces. State why a rejected
alternative loses and which changed assumption would make it preferable. Avoid
unsupported numerical scores that conceal uncertainty.

## Define the operating process

Name activities and their outputs: clarify needs, evaluate design/risks, build,
integrate, verify, obtain user feedback, release, and maintain as applicable.
Place each activity in the chosen cycle or phase; assign owners only where
known. Reuse artifacts the project already maintains. For every handoff or
review, identify its consumer and deciding evidence, not a required meeting.

Specify how feedback is collected, when it changes scope or priority, and how
affected requirements, tests, dependencies, and release decisions are updated.
If real users are unavailable, state the proxy evidence and its limitations,
and identify when actual acceptance must occur. A prototype is not that
acceptance unless it exercises the required user task under agreed conditions.

Example: stable reporting rules with an unproven external API favor a bounded
integration experiment before committing to sequential delivery. Stable rules
do not remove technical risk. Changing onboarding needs with accessible users
favor short usable increments reviewed against task success; feed observations
into prioritized requirements before the next increment, not an unbounded
mid-slice rewrite.

Reassess when feedback access disappears, requirements churn changes, an
integration assumption fails, evidence arrives too late, or release constraints
shift. State the observable trigger and the decision to revisit. Finish with
the selected process, alternatives, assumptions, activities/artifacts, feedback
path, change handling, and reassessment triggers. Implementation and scheduling
remain separate requests.

Sources: [Agile principles][agile] support feedback and working software;
[Boehm's spiral refinements][spiral] support risk-driven selection. Read
[Royce's original paper][royce] for its warning about late verification, not as
a universal mandate for documentation volume or rigid one-pass development.

[agile]: https://agilemanifesto.org/principles.html
[spiral]: https://www.sei.cmu.edu/library/spiral-development-experience-principles-and-refinements-spiral-development-workshop-february-9-2000/
[royce]: https://blog.marsen.me/assets/royce1970.pdf
