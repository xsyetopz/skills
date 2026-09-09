---
name: legacy-cleanup
description:
  Remove confirmed obsolete aliases, shims, entrypoints, or compatibility paths
  after their consumers are gone. Excludes active migrations and still-supported
  contracts.
---

# Legacy Cleanup

For each candidate, establish its replacement, exposure, consumers, and
retirement evidence. Trace imports, exports, configuration, generated
registries, tests, packaging, and supported external contracts.

Read [removal evidence](references/removal-evidence.md) for dynamic consumers,
published exports, generated artifacts, and persisted values.

Remove confirmed obsolete surfaces with their dedicated resources and active
documentation routes. Remove forwarding wrappers, hidden aliases, and fallbacks
when complete retirement is requested. Keep historical release facts and
provenance.

An active consumer requires migration before removal. Identify that dependency
and continue independent cleanup. Missing text matches alone do not establish
retirement.

Check retained consumers and the resulting package/export surface. Verify that
active routes no longer reference deleted resources. Report completed removals
and unresolved candidates with their evidence.
