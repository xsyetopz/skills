# Failure modes and recovery

| Failure mode | What it looks like | Required recovery |
| --- | --- | --- |
| **Sink-name finding** | A dangerous function name becomes a finding without input/reachability. | Trace the full path and property. |
| **Auth bypass for testing** | Security checks are disabled to make a reproduction work. | Use legitimate test identities and isolated fixtures. |
| **Unsafe composite** | Several allowed actions combine into unauthorized extraction or mutation. | Evaluate end-to-end authorization. |
| **Scanner authority** | Tool severity/output is copied without source validation and local analysis. | Verify version, path, reachability, and impact. |
| **Secret leakage** | Tokens or sensitive payloads enter commands, logs, or reports. | Redact and use approved secret handling. |
| **Compliance inflation** | A code review is reported as certification. | State exact controls/evidence and missing audit scope. |
| **Mitigation assumption** | Proxy/WAF/sandbox is assumed deployed and effective. | Inspect actual configuration and bypass conditions. |

## Recovery discipline

Preserve the first useful error and the state that produced it. Stop dependent
work when a prerequisite is false. Change strategy when another equivalent edit
or retry cannot produce new evidence. Undo only attributable experimental
changes; never reset or overwrite unrelated user work to obtain a clean result.

Do not convert a failure into success by swallowing the error, weakening the
assertion, regenerating an unexplained snapshot, adding speculative fallback
behavior, or reporting an intermediate checkpoint as the completed task.
