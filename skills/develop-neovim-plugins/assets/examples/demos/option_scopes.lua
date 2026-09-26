-- nvim --clean --headless -l option_scopes.lua
-- Where each Lua option interface writes, observed with two windows.
local api = vim.api
vim.cmd("vsplit")
local w1 = api.nvim_get_current_win()
local w2 = vim.fn.win_getid(vim.fn.winnr("#"))

local function report(label)
  print(("%-28s w1=%-5s w2=%-5s global=%s"):format(label,
    tostring(vim.wo[w1].wrap), tostring(vim.wo[w2].wrap),
    tostring(vim.go.wrap)))
end

report("default")
vim.opt_local.wrap = false          -- like :setlocal nowrap
report("vim.opt_local.wrap=false")
vim.opt_local.wrap = true
vim.o.wrap = false                  -- like :set nowrap
report("vim.o.wrap=false")
vim.cmd("new")                      -- a new window inherits the global
print(("new window after vim.o: wrap=%s"):format(tostring(vim.wo.wrap)))
assert(vim.wo.wrap == false)

-- Buffer options: vim.bo[buf] needs a handle, not the current buffer.
local scratch = api.nvim_create_buf(false, true)
vim.bo[scratch].filetype = "text"
print(("vim.bo[scratch].filetype=%s current=%q"):format(
  vim.bo[scratch].filetype, vim.bo.filetype))

-- vim.opt returns an Option object; vim.o returns the value.
print(("type(vim.o.shortmess)=%s type(vim.opt.shortmess)=%s"):format(
  type(vim.o.shortmess), type(vim.opt.shortmess)))
local ok, err = pcall(function() return vim.o.not_an_option end)
print("vim.o.not_an_option -> " .. tostring(err))
assert(not ok)
