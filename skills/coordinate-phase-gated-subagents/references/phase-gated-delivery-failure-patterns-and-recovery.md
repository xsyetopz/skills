# Failure patterns and recovery for Phase Gated Delivery

| Failure mode | What it looks like | Required recovery |
| --- | --- | --- |
| **Agent proliferation** | Many children perform work one capable agent could finish faster. | Collapse work and keep only assignments with distinct value. |
| **Duplicate reconnaissance** | Each child rereads the same code and produces overlapping summaries. | Share inspected context and partition questions. |
| **Conflicting writes** | Children change the same files or contract independently. | Stop, preserve both diffs, choose an owner, and integrate deliberately. |
| **Lost result** | A child completes but the coordinator advances without persisting or reading it. | Consume the result immediately and record relevant evidence. |
| **Review quota** | Reviewers are added to satisfy a count or forced to invent findings. | Use a distinct review question or no extra reviewer. |
| **Prompt-only cancellation** | The coordinator assumes a short prompt or ignored response stopped a worker. | Use actual cancel/timeout controls and verify terminal state. |
| **Phase laundering** | Later work begins because one check passed while another required check was unattempted. | Keep the gate open and record the missing evidence. |

## Recovery discipline

Preserve the first observable multi-agent phase coordination failure and the
state that produced it. Stop dependent work after a false prerequisite. If
another equivalent retry cannot add evidence, change the source, instrument, or
hypothesis. Undo only task-owned experiments; preserve unrelated user work.

Do not make the multi-agent phase coordination appear successful by swallowing
its error, weakening its oracle, regenerating an unexplained snapshot, adding an
unsupported fallback, or reporting an intermediate checkpoint as completion.
