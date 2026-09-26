-- Runs for every buffer whose 'filetype' becomes "lineuplog".
-- Everything here is buffer- or window-local and undone by b:undo_ftplugin.
if vim.b.did_ftplugin then
  return
end
vim.b.did_ftplugin = 1

vim.opt_local.wrap = false
vim.opt_local.number = false
vim.keymap.set("n", "q", "<Cmd>close<CR>", {
  buf = 0,
  desc = "lineup: close the log window",
})

vim.b.undo_ftplugin = "setlocal wrap< number<"
  .. " | silent! nunmap <buffer> q"
