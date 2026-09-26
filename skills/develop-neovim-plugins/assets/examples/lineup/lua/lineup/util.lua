-- Pure Lua 5.1 helpers: no `vim`, no `//`, no bitwise operators, no `utf8`,
-- no `table.unpack`, no `goto`. Tested under nvim (LuaJIT) and lua 5.4.
local M = {}

---Copy `defaults`, overlay `user`, and report keys that `defaults` lacks.
---Nested tables are replaced, not merged: list options stay predictable.
---@param defaults table<string, any>
---@param user table<string, any>?
---@return table<string, any> merged
---@return string[] unknown sorted unknown keys
function M.merge(defaults, user)
  local merged, unknown = {}, {}
  for key, value in pairs(defaults) do
    merged[key] = value
  end
  for key, value in pairs(user or {}) do
    if defaults[key] == nil then
      unknown[#unknown + 1] = tostring(key)
    else
      merged[key] = value
    end
  end
  table.sort(unknown)
  return merged, unknown
end

---Split process output into buffer lines, dropping one trailing newline.
---@param text string
---@return string[]
function M.split_lines(text)
  local lines = {}
  text = text:gsub("\n$", "")
  for line in (text .. "\n"):gmatch("(.-)\n") do
    lines[#lines + 1] = line
  end
  return lines
end

---Names from `candidates` that start with `prefix`, in input order.
---@param candidates string[]
---@param prefix string
---@return string[]
function M.prefix_matches(candidates, prefix)
  local out = {}
  for _, name in ipairs(candidates) do
    if name:sub(1, #prefix) == prefix then
      out[#out + 1] = name
    end
  end
  return out
end

return M
