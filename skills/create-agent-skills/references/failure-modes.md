# Failure modes and recovery

| Failure mode | What it looks like | Required recovery |
| --- | --- | --- |
| **Topic-only generation** | A skill repeats generic advice without real APIs, examples, or failure evidence. | Research actual tasks, target repos, and authoritative sources first. |
| **Description catchall** | Broad keywords activate the skill for unrelated tasks. | Use intent, outputs, and exclusions; test near misses. |
| **Reference dumping** | Every reference loads or long manuals are copied without routing. | Gate references by task condition and extract the non-obvious operational knowledge. |
| **Resource deletion** | Scripts/assets are removed because the rewritten body no longer mentions them. | Inspect function/callers and retain, repair, or replace based on capability. |
| **Static-eval inflation** | Line counts, tests, or valid frontmatter are reported as one-shot reliability. | Run actual activation and task evaluations. |
| **Custom framework creep** | New manifests, routers, schemas, or process layers are added without a consumer. | Use the standard structure and native harness metadata. |
| **Example cargo cult** | A public skill’s staffing, file layout, or commands become universal requirements. | Adopt only the pattern whose rationale applies. |

## Recovery discipline

Preserve the first useful error and the state that produced it. Stop dependent
work when a prerequisite is false. Change strategy when another equivalent edit
or retry cannot produce new evidence. Undo only attributable experimental
changes; never reset or overwrite unrelated user work to obtain a clean result.

Do not convert a failure into success by swallowing the error, weakening the
assertion, regenerating an unexplained snapshot, adding speculative fallback
behavior, or reporting an intermediate checkpoint as the completed task.
