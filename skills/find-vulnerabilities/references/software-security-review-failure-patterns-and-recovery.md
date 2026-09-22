# Failure patterns and recovery for Software Security Review

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

Preserve the first observable security finding failure and the state that
produced it. Stop dependent work after a false prerequisite. If another
equivalent retry cannot add evidence, change the source, instrument, or
hypothesis. Undo only task-owned experiments; preserve unrelated user work.

Do not make the security finding appear successful by swallowing its error,
weakening its oracle, regenerating an unexplained snapshot, adding an
unsupported fallback, or reporting an intermediate checkpoint as completion.
