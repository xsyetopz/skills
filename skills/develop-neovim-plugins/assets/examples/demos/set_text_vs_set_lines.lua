-- nvim --clean --headless -l set_text_vs_set_lines.lua
-- Changing one word: set_lines replaces the whole line, set_text only the
-- bytes. An extmark after the word survives only the set_text edit.
local api = vim.api
local ns = api.nvim_create_namespace("demo.set_text")

local function run(edit)
  local buf = api.nvim_create_buf(false, true)
  api.nvim_buf_set_lines(buf, 0, -1, true, { "local foo = 1" })
  -- mark on "1" (row 0, byte col 12)
  local id = api.nvim_buf_set_extmark(buf, ns, 0, 12, {})
  edit(buf)
  local pos = api.nvim_buf_get_extmark_by_id(buf, ns, id, {})
  return api.nvim_buf_get_lines(buf, 0, -1, true)[1], pos[2]
end

local text1, col1 = run(function(buf)
  api.nvim_buf_set_lines(buf, 0, 1, true, { "local bar = 1" })
end)
local text2, col2 = run(function(buf)
  api.nvim_buf_set_text(buf, 0, 6, 0, 9, { "bar" }) -- bytes 6..8, end excl.
end)
assert(text1 == text2 and text1 == "local bar = 1")
print(("set_lines: %q extmark col %d"):format(text1, col1))
print(("set_text:  %q extmark col %d"):format(text2, col2))
assert(col2 == 12, "set_text must keep the mark on '1'")
