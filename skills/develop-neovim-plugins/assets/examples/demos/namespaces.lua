-- nvim --clean --headless -l namespaces.lua
-- Own a namespace for extmarks and diagnostics; clear only that namespace.
local api = vim.api
local mine = api.nvim_create_namespace("demo.mine")
local other = api.nvim_create_namespace("demo.other")
local buf = api.nvim_get_current_buf()
api.nvim_buf_set_lines(buf, 0, -1, true, { "alpha beta", "gamma" })

-- Extmarks: 0-based row and byte column; gravity decides insert behavior.
api.nvim_buf_set_extmark(buf, mine, 0, 6, { end_col = 10, hl_group = "Todo" })
local left = api.nvim_buf_set_extmark(buf, mine, 0, 6,
  { right_gravity = false })
local right = api.nvim_buf_set_extmark(buf, mine, 0, 6, {})
api.nvim_buf_set_extmark(buf, other, 1, 0, {})
api.nvim_buf_set_text(buf, 0, 6, 0, 6, { "NEW " }) -- insert at the marks
print(("insert at col 6: left-gravity col %d, right-gravity col %d"):format(
  api.nvim_buf_get_extmark_by_id(buf, mine, left, {})[2],
  api.nvim_buf_get_extmark_by_id(buf, mine, right, {})[2]))

-- Diagnostics: 0-based lnum/col, one namespace per producer.
vim.diagnostic.set(mine, buf, { { lnum = 0, col = 0, message = "mine" } })
vim.diagnostic.set(other, buf, { { lnum = 1, col = 0, message = "other" } })

api.nvim_buf_clear_namespace(buf, mine, 0, -1)
vim.diagnostic.reset(mine, buf)
local function count_marks(ns)
  return #api.nvim_buf_get_extmarks(buf, ns, 0, -1, {})
end
print(("after clearing mine: extmarks mine=%d other=%d"):format(
  count_marks(mine), count_marks(other)))
print(("after reset(mine): diagnostics mine=%d other=%d"):format(
  #vim.diagnostic.get(buf, { namespace = mine }),
  #vim.diagnostic.get(buf, { namespace = other })))
assert(count_marks(mine) == 0 and count_marks(other) == 1)
assert(#vim.diagnostic.get(buf, { namespace = other }) == 1)

-- Cursor is (1,0)-indexed; buffer API rows are 0-based.
api.nvim_win_set_cursor(0, { 2, 0 })
local row = api.nvim_win_get_cursor(0)[1]
print(("cursor row %d -> buffer line %q"):format(row,
  api.nvim_buf_get_lines(buf, row - 1, row, true)[1]))
