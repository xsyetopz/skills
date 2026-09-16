# Failure modes and recovery

| Failure mode | What it looks like | Required recovery |
| --- | --- | --- |
| **Current-buffer race** | Callback edits whichever buffer is active later. | Use captured handle and freshness checks. |
| **Global autocmd deletion** | Reload/cleanup removes user/other plugin events. | Own a named augroup. |
| **Fast-event API misuse** | Callback calls forbidden API directly. | Schedule to main loop. |
| **Handle leak** | Timer/job/uv handle stays open after unload. | Stop/close and test lifecycle. |
| **Vim/Neovim conflation** | Vimscript/Vim API assumptions conflict with Neovim Lua API. | Use target host/version. |
| **Config swallowing** | Unknown option is ignored. | Validate/error or preserve native escape hatch. |

## Recovery discipline

Preserve the first useful error and the state that produced it. Stop dependent
work when a prerequisite is false. Change strategy when another equivalent edit
or retry cannot produce new evidence. Undo only attributable experimental
changes; never reset or overwrite unrelated user work to obtain a clean result.

Do not convert a failure into success by swallowing the error, weakening the
assertion, regenerating an unexplained snapshot, adding speculative fallback
behavior, or reporting an intermediate checkpoint as the completed task.
