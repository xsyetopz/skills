# Verification and evidence

Select evidence at the boundary of the claim. Run the smallest sufficient set
first, then broaden only when the change crosses another contract boundary.

| Claim | Sufficient evidence | Not sufficient by itself |
| --- | --- | --- |
| Command/autocmd works | Headless or real Neovim invocation and observed buffer/window/result. | Lua module unit test only. |
| Stale result suppressed | Headless test edits/replaces buffer before callback and observes no stale mutation. | changedtick read in source. |
| Reload safe | Source/reload/teardown twice without duplicates/leaks. | First load passes. |
| Resource cleanup | Jobs/timers/handles terminate/close on teardown and errors. | Process exits eventually. |
| Version support | Test declared minimum/current versions or CI matrix. | Newest local Neovim. |
| Distribution | Clean runtimepath installation, help tags, module load, and dependencies. | Files copied. |

## Command patterns

Use the repository’s existing commands. Record the exact command, working
directory, revision, configuration, and result.

## Result reporting

Separate authored checks, executed checks, static analysis, simulation,
integration/host execution, production observations, skipped checks, and
unavailable checks. Include relevant failure output. A green check establishes
only the properties it can discriminate; a single flaky pass, successful parser,
or valid configuration file is not broad runtime proof.
