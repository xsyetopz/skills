local M = {}

---Replace a one-based inclusive line range with a JSON array of those lines.
---@param first integer
---@param last integer
function M.encode_lines(first, last)
  local lines = vim.api.nvim_buf_get_lines(0, first - 1, last, true)
  local encoded = vim.json.encode(lines)
  vim.api.nvim_buf_set_lines(0, first - 1, last, true, { encoded })
end

return M
