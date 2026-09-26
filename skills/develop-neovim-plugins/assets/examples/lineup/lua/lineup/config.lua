-- Configuration only: no autocmds, commands, or processes are created here.
-- Sources, lowest to highest precedence: defaults, vim.g.lineup, setup().
local util = require("lineup.util")

---@class (exact) lineup.Config
---@field filters string[] programs offered by :LineupFilter completion
---@field timeout_ms integer kill a filter after this many milliseconds

---@class (exact) lineup.UserConfig
---@field filters? string[]
---@field timeout_ms? integer

local M = {}

---@type lineup.Config
M.defaults = { filters = { "sort", "uniq" }, timeout_ms = 5000 }

---@type lineup.UserConfig?
local overrides = nil

---@param list any
---@return boolean ok
---@return string? message
local function is_string_list(list)
  if not vim.islist(list) then
    return false, "a list"
  end
  for _, item in ipairs(list) do
    if type(item) ~= "string" then
      return false, "a list of strings"
    end
  end
  return true
end

---Validate a merged configuration; raise a Lua error naming the bad field.
---@param config table
---@return lineup.Config
function M.validate(config)
  vim.validate("lineup.filters", config.filters, is_string_list)
  vim.validate("lineup.timeout_ms", config.timeout_ms, function(v)
    return type(v) == "number" and v > 0 and v % 1 == 0
  end, "positive integer")
  return config
end

---Store overrides. Does not initialize anything (:h lua-plugin-init).
---@param opts lineup.UserConfig?
function M.setup(opts)
  vim.validate("opts", opts, "table", true)
  overrides = opts
end

---Resolve the effective configuration now (vim.g may change at runtime).
---@return lineup.Config config
---@return string[] unknown keys the user set that lineup does not know
function M.get()
  local merged, unknown_g = util.merge(M.defaults, vim.g.lineup)
  local final, unknown_s = util.merge(merged, overrides)
  for _, key in ipairs(unknown_s) do
    unknown_g[#unknown_g + 1] = key
  end
  return M.validate(final), unknown_g
end

return M
