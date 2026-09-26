-- LuaRocks package description. File name: <package>-<version>.rockspec.
-- Replace OWNER before publishing; `luarocks lint` checks the fields.
rockspec_format = "3.0"
package = "lineup"
version = "scm-1"
source = {
  url = "git+https://github.com/OWNER/lineup",
}
description = {
  summary = "Encode or filter Neovim buffer lines",
  license = "MIT",
  labels = { "neovim" },
}
dependencies = {
  "lua >= 5.1",
}
build = {
  type = "builtin",
  modules = {
    ["lineup"] = "lua/lineup/init.lua",
    ["lineup.config"] = "lua/lineup/config.lua",
    ["lineup.health"] = "lua/lineup/health.lua",
    ["lineup.util"] = "lua/lineup/util.lua",
  },
  copy_directories = { "doc", "ftplugin", "plugin" },
}
