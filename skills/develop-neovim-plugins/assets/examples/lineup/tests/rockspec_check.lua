-- Structural check of the rockspec without luarocks (PUC Lua or nvim -l):
-- mandatory fields, file name, and every module/directory path exists.
local here = arg[0]:match("^(.*)/[^/]*$") or "."
local root = here .. "/.."
local name = "lineup-scm-1.rockspec"
local spec = {}
local chunk = assert(loadfile(root .. "/" .. name, "t", spec))
chunk()
-- Mandatory per docs/rockspec_format.md: package, version, source.url.
for _, field in ipairs({ "package", "version", "source" }) do
  assert(spec[field] ~= nil, "missing field " .. field)
end
assert(spec.source.url, "missing source.url")
assert(spec.build and spec.build.type == "builtin", "expected builtin build")
assert(name == spec.package .. "-" .. spec.version .. ".rockspec",
  "file name must be <package>-<version>.rockspec")
local function exists(path)
  local f = io.open(root .. "/" .. path, "r")
  if f then
    f:close()
  end
  return f ~= nil
end
local count = 0
for module, path in pairs(spec.build.modules) do
  assert(exists(path), module .. " -> missing " .. path)
  count = count + 1
end
local reserved = { lua = true, lib = true, rock_manifest = true }
for _, dir in ipairs(spec.build.copy_directories) do
  assert(not reserved[dir], "reserved copy_directories name " .. dir)
  assert(exists(dir .. "/lineup.lua") or exists(dir .. "/lineup.txt")
    or exists(dir .. "/lineuplog.lua"), "empty directory " .. dir)
end
print(("PASS rockspec: %d modules, %d directories"):format(count,
  #spec.build.copy_directories))
