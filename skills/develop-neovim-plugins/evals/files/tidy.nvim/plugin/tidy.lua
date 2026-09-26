vim.api.nvim_create_user_command('Tidy', function()
  require('tidy').run()
end, { desc = 'Format the current HTML buffer with tidy' })
