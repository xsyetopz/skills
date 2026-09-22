# Extension failures and recovery for Neovim Lua Plugin

| Failure mode | What it looks like | Required recovery |
| --- | --- | --- |
| **Current-buffer race** | Callback edits whichever buffer is active later. | Use captured handle and freshness checks. |
| **Global autocmd deletion** | Reload/cleanup removes user/other plugin events. | Own a named augroup. |
| **Fast-event API misuse** | Callback calls forbidden API directly. | Schedule to main loop. |
| **Handle leak** | Timer/job/uv handle stays open after unload. | Stop/close and test lifecycle. |
| **Vim/Neovim conflation** | Vimscript/Vim API assumptions conflict with Neovim Lua API. | Use target host/version. |
| **Config swallowing** | Unknown option is ignored. | Validate/error or preserve native escape hatch. |

## Recovery discipline

Preserve the first observable Neovim plugin failure and the state that produced
it. Stop dependent work after a false prerequisite. If another equivalent retry
cannot add evidence, change the source, instrument, or hypothesis. Undo only
task-owned experiments; preserve unrelated user work.

Do not make the Neovim plugin appear successful by swallowing its error,
weakening its oracle, regenerating an unexplained snapshot, adding an
unsupported fallback, or reporting an intermediate checkpoint as completion.
