vim.keymap.set('n', '<leader>n', function()
  require('notes').open_today()
end, { desc = "Open today's note" })

vim.api.nvim_create_user_command('NotesToday', function()
  require('notes').open_today()
end, { desc = "Open today's note" })
