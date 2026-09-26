local fmt = require('fmt')

vim.api.nvim_create_user_command('Fmt', function(cmd)
  fmt.format(0, cmd.line1, cmd.line2)
end, { range = '%', desc = 'Align = signs in the range' })
