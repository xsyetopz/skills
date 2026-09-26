local M = {}

M.cmd = { 'tidy', '-q' }

function M.run()
  local text = table.concat(vim.api.nvim_buf_get_lines(0, 0, -1, false), '\n')
  vim.system(M.cmd, { stdin = text }, function(out)
    vim.schedule(function()
      vim.api.nvim_buf_set_lines(0, 0, -1, false, vim.split(out.stdout, '\n'))
    end)
  end)
end

return M
