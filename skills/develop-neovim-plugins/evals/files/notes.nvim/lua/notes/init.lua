local M = {}

M.dir = vim.fs.joinpath(vim.fn.stdpath('data'), 'notes')

function M.open_today()
  vim.fn.mkdir(M.dir, 'p')
  vim.cmd.edit(vim.fn.fnameescape(vim.fs.joinpath(M.dir, os.date('%Y-%m-%d') .. '.md')))
end

return M
