# Failure modes and recovery

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

Preserve the first useful error and the state that produced it. Stop dependent
work when a prerequisite is false. Change strategy when another equivalent edit
or retry cannot produce new evidence. Undo only attributable experimental
changes; never reset or overwrite unrelated user work to obtain a clean result.

Do not convert a failure into success by swallowing the error, weakening the
assertion, regenerating an unexplained snapshot, adding speculative fallback
behavior, or reporting an intermediate checkpoint as the completed task.
