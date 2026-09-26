-- Pure tests for lua/lineup/util.lua. Run under both runtimes:
--   lua tests/util_spec.lua                 (PUC Lua 5.4)
--   nvim --clean -l tests/util_spec.lua     (LuaJIT, Lua 5.1 semantics)
local here = arg and arg[0] and arg[0]:match("^(.*)/[^/]*$") or "."
package.path = here .. "/../lua/?.lua;" .. package.path
local util = require("lineup.util")

local function same(a, b)
  if #a ~= #b then
    return false
  end
  for i = 1, #a do
    if a[i] ~= b[i] then
      return false
    end
  end
  return true
end

local cases = {
  function()
    local merged, unknown =
      util.merge({ a = 1, b = 2 }, { b = 3, zz = 1, c = 0 })
    assert(merged.a == 1 and merged.b == 3 and merged.c == nil, "merge")
    assert(same(unknown, { "c", "zz" }), table.concat(unknown, ","))
  end,
  function()
    local merged, unknown = util.merge({ a = 1 }, nil)
    assert(merged.a == 1 and #unknown == 0, "nil user config")
  end,
  function()
    assert(same(util.split_lines("b\na\n"), { "b", "a" }), "trailing newline")
    assert(same(util.split_lines("x\n\ny"), { "x", "", "y" }), "empty line")
    assert(same(util.split_lines(""), { "" }), "empty output is one empty line")
  end,
  function()
    local got = util.prefix_matches({ "sort", "uniq", "sed" }, "s")
    assert(same(got, { "sort", "sed" }), "prefix")
  end,
}

for i, case in ipairs(cases) do
  case()
  print(("ok util %d"):format(i))
end
print(("PASS util_spec under %s"):format(jit and jit.version or _VERSION))
