-- One module: requires as locals, local constants, the module table,
-- types, local helpers, public functions, and a single return.
local string_format = string.format

local PRIVATE_CONSTANT = 1

local M = {}

M.PUBLIC_CONSTANT = 2

local PublicType = {}
PublicType.__index = PublicType

function PublicType.new(value)
    return setmetatable({ value = value or PRIVATE_CONSTANT }, PublicType)
end

function PublicType:describe()
    return string_format("PublicType(%d)", self.value)
end

local function private_helper(value)
    return value * M.PUBLIC_CONSTANT
end

function M.public_function(value)
    return PublicType.new(private_helper(value))
end

M.PublicType = PublicType

return M
