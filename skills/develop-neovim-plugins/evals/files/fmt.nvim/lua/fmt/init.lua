local M = {}

-- Building the alignment table is the expensive part of loading this module.
local widths = {}
for i = 1, 200000 do
  widths[i] = vim.fn.strdisplaywidth(string.rep('x', i % 40))
end

function M.format(buf, first, last)
  local lines = vim.api.nvim_buf_get_lines(buf, first - 1, last, false)
  local col = 0
  for _, line in ipairs(lines) do
    local at = line:find('=', 1, true)
    if at and at > col then
      col = at
    end
  end
  for i, line in ipairs(lines) do
    local at = line:find('=', 1, true)
    if at then
      lines[i] = line:sub(1, at - 1) .. string.rep(' ', col - at) .. line:sub(at)
    end
  end
  vim.api.nvim_buf_set_lines(buf, first - 1, last, false, lines)
end

M._widths = widths
return M
