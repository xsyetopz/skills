if vim.g.loaded_example_plugin == 1 then
  return
end
vim.g.loaded_example_plugin = 1

vim.api.nvim_create_user_command("ExampleJsonLines", function(command)
  require("example").encode_lines(command.line1, command.line2)
end, {
  range = true,
  desc = "Encode the selected lines as a JSON array",
})
