# DuckStation failure patterns and recovery

Common competing causes are wrong BIOS/region, invalid or compressed image,
per-game override, renderer backend difference, stale shader/texture cache,
patch address/condition error, host GPU/driver issue, or save-state/version
mismatch. Preserve the original failure signature while testing them. Do not
clear ordinary user data, rewrite saves, or replace configuration to make a
diagnostic run succeed.

1. Reproduce with the original revision, input, and isolated copied state.
1. Capture the first failing boundary: configure, compile/link, frontend start,
   guest boot, guest execution, renderer output, patch/texture load, or save
   restore.
1. Reset one owned cache or override at a time. Re-run the same signature check.
1. Compare a known-good revision/configuration only when the same legal input
   and evidence boundary are available.
1. Recover by removing only task-created state or restoring the copied setting.
   Record what was changed and whether user data remained untouched.

A retry that happens to pass is not a root cause. A different image, BIOS,
renderer, or save state is a changed experiment unless that variable is the
explicit hypothesis.
