vim.api.nvim_create_autocmd('BufWritePost', {
  pattern = '*.md',
  callback = function(a)
    require('mdlint').run(a.buf)
  end,
})

vim.api.nvim_create_user_command('MdlintRun', function()
  require('mdlint').run(vim.api.nvim_get_current_buf())
end, { desc = 'Lint the current Markdown buffer' })
