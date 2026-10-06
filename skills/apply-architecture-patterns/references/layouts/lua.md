# Lua

A lexical `local` is the privacy mechanism.
A name is `local` unless module consumers need it.
Public names are fields on the module table that the file returns.
Lua 5.5 adds `global` declarations; a module still uses `local` and returns one table.

## Order in a file

1. `require` calls, each assigned to a `local`.
1. Local constants.
1. The module table, `local M = {}`.
1. Local types: a table with `__index`, its constructor, then its methods.
1. Local helper functions, before the functions that call them.
1. Exported functions and fields on `M`.
1. `return M` as the last statement.

A local must be defined above its first use, so helpers come first.
Export a type by assigning it to `M` under its own name.
Tests go in `spec/` (busted) or the directory the project's runner uses.

```lua
local dependency = require("dependency")

local PRIVATE_CONSTANT = 1

local M = {}

M.PUBLIC_CONSTANT = 2

local Widget = {}
Widget.__index = Widget

function Widget.new()
    return setmetatable({ count = PRIVATE_CONSTANT }, Widget)
end

function Widget:increment()
    self.count = self.count + 1
end

local function private_helper(widget)
    widget:increment()
    return dependency.wrap(widget)
end

function M.public_function()
    return private_helper(Widget.new())
end

M.Widget = Widget

return M
```
