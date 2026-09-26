-- Checks an installed copy (only plugin/ lua/ ftplugin/ doc/) on a clean
-- 'runtimepath', so a source checkout cannot mask a missing file:
--   nvim --clean --headless --cmd "set rtp^=PKG" -l installed_check.lua
local function one(path)
  local found = vim.api.nvim_get_runtime_file(path, false)[1]
  assert(found, "not on runtimepath: " .. path)
  return found
end
assert(vim.fn.exists(":LineupJson") == 2, ":LineupJson missing")
one("ftplugin/lineuplog.lua")
one("lua/lineup/health.lua")
local doc = vim.fn.fnamemodify(one("doc/lineup.txt"), ":h")
vim.cmd.helptags(vim.fn.fnameescape(doc))
vim.cmd.help(":LineupFilter")
assert(vim.bo.filetype == "help", ":help :LineupFilter did not resolve")
vim.cmd.helpclose()
vim.cmd.enew()
vim.api.nvim_buf_set_lines(0, 0, -1, true, { "a" })
vim.cmd("LineupJson")
assert(vim.api.nvim_get_current_line() == '["a"]', "command failed")
print("PASS installed layout: " .. vim.fn.fnamemodify(doc, ":h:t"))
