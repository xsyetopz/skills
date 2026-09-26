local M = {}

local ns = vim.api.nvim_create_namespace('mdlint')

function M.run(buf)
  local diags = {}
  for i, line in ipairs(vim.api.nvim_buf_get_lines(buf, 0, -1, false)) do
    if #line > 100 then
      diags[#diags + 1] = { lnum = i - 1, col = 100, message = 'line longer than 100', severity = vim.diagnostic.severity.WARN }
    end
  end
  vim.diagnostic.set(ns, buf, diags)
end

return M
