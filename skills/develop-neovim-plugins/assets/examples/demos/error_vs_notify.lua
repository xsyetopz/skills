-- nvim --clean --headless -l error_vs_notify.lua
-- What a caller sees when a command fails via error() versus vim.notify().
local api = vim.api
local after = false
api.nvim_create_user_command("DemoError", function()
  error("config file missing")
end, {})
api.nvim_create_user_command("DemoNotify", function()
  vim.notify("demo: config file missing", vim.log.levels.ERROR)
  after = true -- notify does not unwind the callback
end, {})

local function first_line(s)
  return (tostring(s):match("[^\n]*"):gsub("^.*nvim_exec2%(%), line 1: ", ""))
end

local ok, err = pcall(vim.cmd, "DemoError")
print(("error():  ok=%s traceback=%s"):format(tostring(ok),
  tostring(tostring(err):find("stack traceback", 1, true) ~= nil)))
print("  " .. first_line(err))

ok, err = pcall(vim.cmd, "DemoNotify")
print(("notify(): ok=%s traceback=%s callback finished=%s"):format(
  tostring(ok), tostring(tostring(err):find("stack traceback", 1, true)
    ~= nil), tostring(after)))
print("  " .. first_line(err))
assert(after and not tostring(err):find("stack traceback", 1, true))
