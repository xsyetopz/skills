-- :checkhealth lineup finds this module on 'runtimepath' and calls check().
-- Read-only: it reports; it never changes configuration or state.
local M = {}

function M.check()
  vim.health.start("lineup")
  if vim.fn.has("nvim-0.12") == 1 then
    vim.health.ok("Neovim 0.12 or newer")
  else
    vim.health.error("Neovim 0.12 or newer is required",
      "Upgrade Neovim; lineup uses the 0.12 `buf` keymap option.")
  end

  local ok, cfg, unknown = pcall(require("lineup.config").get)
  if not ok then
    vim.health.error("invalid configuration: " .. tostring(cfg),
      "Fix vim.g.lineup or the table passed to setup().")
    return
  end
  vim.health.ok("configuration is valid")
  for _, key in ipairs(unknown) do
    vim.health.warn("unknown option: " .. key, "Remove it or fix the typo.")
  end

  for _, program in ipairs(cfg.filters) do
    if vim.fn.executable(program) == 1 then
      vim.health.ok(("filter `%s` found"):format(program))
    else
      vim.health.warn(("filter `%s` is not executable"):format(program),
        "Install it or remove it from `filters`.")
    end
  end
end

return M
