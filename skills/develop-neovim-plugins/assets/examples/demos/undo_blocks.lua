-- nvim --clean --headless -l undo_blocks.lua
-- API edits in one script run share an undo block until something closes
-- it; setting 'undolevels' closes the block (:h undo-close-block).
local api = vim.api
local function seq()
  return vim.fn.undotree().seq_last
end

local base = seq()
api.nvim_buf_set_lines(0, 0, -1, true, { "a" })
api.nvim_buf_set_lines(0, 1, 1, true, { "b" })
print(("two edits, no close:  %d undo step(s)"):format(seq() - base))
assert(seq() - base == 1)

base = seq()
vim.o.undolevels = vim.o.undolevels
api.nvim_buf_set_lines(0, 0, 0, true, { "c" })
vim.o.undolevels = vim.o.undolevels
api.nvim_buf_set_lines(0, 0, 0, true, { "d" })
print(("two edits, closed:    %d undo step(s)"):format(seq() - base))
assert(seq() - base == 2)

-- A scratch buffer with undolevels=-1 records nothing.
local log = api.nvim_create_buf(false, true)
vim.bo[log].undolevels = -1
api.nvim_buf_call(log, function()
  base = seq()
  api.nvim_buf_set_lines(log, 0, -1, true, { "x" })
  print(("undolevels=-1 buffer: %d undo step(s)"):format(seq() - base))
  assert(seq() - base == 0)
end)
