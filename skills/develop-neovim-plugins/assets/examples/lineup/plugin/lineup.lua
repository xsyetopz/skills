-- Startup entry point. Neovim sources every plugin/*.lua on 'runtimepath'
-- at startup, so this file only registers commands and <Plug> mappings.
-- Each callback requires the implementation on first use (:h lua-plugin-lazy).
if vim.g.loaded_lineup then
  return
end
vim.g.loaded_lineup = true

vim.api.nvim_create_user_command("LineupJson", function(cmd)
  require("lineup").json_lines(0, cmd.line1, cmd.line2)
end, {
  range = true,
  desc = "Replace the range with one JSON array of its lines",
})

vim.api.nvim_create_user_command("LineupFilter", function(cmd)
  require("lineup").filter_command(cmd.fargs)
end, {
  nargs = "+",
  desc = "Pipe the buffer through a program; apply output if unchanged",
  complete = function(arg_lead, cmd_line)
    -- Complete only the program name (first argument).
    if cmd_line:match("^%s*%S+%s+%S*$") == nil then
      return {}
    end
    return require("lineup").complete_filter(arg_lead)
  end,
})

vim.api.nvim_create_user_command("LineupLog", function()
  require("lineup").open_log()
end, { nargs = 0, desc = "Show lineup filter runs" })

vim.keymap.set("n", "<Plug>(LineupJson)", "<Cmd>LineupJson<CR>", {
  desc = "lineup: JSON-encode the current line",
})
vim.keymap.set("x", "<Plug>(LineupJson)", ":LineupJson<CR>", {
  silent = true,
  desc = "lineup: JSON-encode the selected lines",
})
