-- Used with: nvim --clean --headless -u tests/minimal_init.lua -l FILE
-- --clean drops the user's config and ShaDa; this adds only the plugin.
local root = vim.fn.fnamemodify(debug.getinfo(1, "S").source:sub(2), ":p:h:h")
vim.opt.runtimepath:prepend(root)
vim.o.swapfile = false
