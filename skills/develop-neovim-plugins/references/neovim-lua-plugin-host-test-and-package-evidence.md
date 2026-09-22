# Host test and package evidence for Neovim Lua Plugin

Select evidence that can discriminate the claimed property of the Neovim plugin.
Run the smallest sufficient check first. Broaden only when another contract
boundary changed.

| Claim | Sufficient evidence | Not sufficient by itself |
| --- | --- | --- |
| Command/autocmd works | Headless or real Neovim invocation and observed buffer/window/result. | Lua module unit test only. |
| Stale result suppressed | Headless test edits/replaces buffer before callback and observes no stale mutation. | changedtick read in source. |
| Reload safe | Source/reload/teardown twice without duplicates/leaks. | First load passes. |
| Resource cleanup | Jobs/timers/handles terminate/close on teardown and errors. | Process exits eventually. |
| Version support | Test declared minimum/current versions or CI matrix. | Newest local Neovim. |
| Distribution | Clean runtimepath installation, help tags, module load, and dependencies. | Files copied. |

## Command patterns

Use the repository's existing commands. Record the exact command, working
directory, revision, configuration, and result.

## Result reporting

For the Neovim plugin, separate authored checks, executed checks, static
analysis, simulation, host/integration execution, production observations,
skips, and unavailable checks. Include useful failure output. A green check
establishes only the property that it can discriminate.
