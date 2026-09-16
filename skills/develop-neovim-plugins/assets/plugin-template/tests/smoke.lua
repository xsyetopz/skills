local function equal(actual, expected, message)
  assert(vim.deep_equal(actual, expected), message .. "\nactual: " .. vim.inspect(actual))
end

local function prepare(lines)
  vim.cmd.enew({ bang = true })
  vim.api.nvim_buf_set_lines(0, 0, -1, true, lines)
  -- End the fixture edit's undo block before exercising the user command.
  vim.cmd("let &undolevels = &undolevels")
end

local function lines()
  return vim.api.nvim_buf_get_lines(0, 0, -1, true)
end

prepare({ "before", 'a"b', "c\\d", "café 雪", "", "after" })
vim.cmd("2,5ExampleJsonLines")
equal(lines(), { "before", '["a\\"b","c\\\\d","café 雪",""]', "after" }, "range bounds or escaping changed")
vim.cmd.undo()
equal(lines(), { "before", 'a"b', "c\\d", "café 雪", "", "after" }, "undo must restore the entire range")
vim.cmd.redo()
equal(lines(), { "before", '["a\\"b","c\\\\d","café 雪",""]', "after" }, "redo must restore the command result")

prepare({ "first", "second", "third" })
vim.api.nvim_win_set_cursor(0, { 2, 0 })
vim.cmd.ExampleJsonLines()
equal(lines(), { "first", '["second"]', "third" }, "default range must be the current line")

prepare({ "" })
vim.cmd("%ExampleJsonLines")
equal(lines(), { '[""]' }, "empty buffer line must be preserved as a string")

prepare({ "unchanged", "also unchanged" })
vim.bo.modifiable = false
local ok = pcall(vim.cmd, "%ExampleJsonLines")
assert(not ok, "nonmodifiable buffers must reject edits")
equal(lines(), { "unchanged", "also unchanged" }, "failed edit must not modify the buffer")
vim.bo.modifiable = true

prepare({ "file is read-only, buffer is modifiable" })
vim.bo.readonly = true
vim.cmd.ExampleJsonLines()
equal(lines(), { '["file is read-only, buffer is modifiable"]' }, "readonly must not be confused with nomodifiable")
vim.bo.readonly = false

vim.cmd("runtime plugin/example.lua")
prepare({ "command still works after repeated loading" })
vim.cmd.ExampleJsonLines()
equal(lines(), { '["command still works after repeated loading"]' }, "repeated loading broke the command")

local root = vim.fn.fnamemodify(debug.getinfo(1, "S").source:sub(2), ":p:h:h")
vim.cmd("helptags " .. vim.fn.fnameescape(root .. "/doc"))
vim.cmd("help :ExampleJsonLines")
assert(vim.bo.filetype == "help", "installed help topic did not resolve")
print("PASS: range, undo/redo, cursor default, empty line, modifiable, readonly, reload, help")
