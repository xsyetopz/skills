-- Implementation, loaded on first use of a command or mapping.
local config = require("lineup.config")
local util = require("lineup.util")

local M = {}

---A request's table identity is its generation token: a completion is
---current only while pending[buf] is still the same table.
---@class lineup.Request
---@field proc vim.SystemObj?

---Pending filter per buffer. Entries are removed on completion and wipeout.
---@type table<integer, lineup.Request>
local pending = {}

---@type string[]
local log = {}
---@type integer?
local log_buf = nil

---@param msg string
---@param level integer
local function notify(msg, level)
  vim.notify("lineup: " .. msg, level)
end

---@param entry string
local function record(entry)
  log[#log + 1] = entry
  if log_buf and vim.api.nvim_buf_is_valid(log_buf) then
    vim.bo[log_buf].modifiable = true
    vim.api.nvim_buf_set_lines(log_buf, 0, -1, true, log)
    vim.bo[log_buf].modifiable = false
  end
end

---Forget a buffer: stop its process and drop its state.
---@param buf integer
function M.forget(buf)
  local req = pending[buf]
  pending[buf] = nil
  if req and req.proc and not req.proc:is_closing() then
    req.proc:kill("sigterm")
  end
end

-- Recreated on every filter run; clear = true keeps exactly one handler.
local function ensure_autocmds()
  local group = vim.api.nvim_create_augroup("lineup", { clear = true })
  vim.api.nvim_create_autocmd("BufWipeout", {
    group = group,
    desc = "lineup: drop per-buffer filter state",
    callback = function(args)
      M.forget(args.buf)
    end,
  })
end

---Replace lines first..last (1-based, inclusive) of `buf` with one JSON
---array of those lines. One user command = one undo step.
---@param buf integer buffer handle, 0 for current
---@param first integer
---@param last integer
function M.json_lines(buf, first, last)
  local lines = vim.api.nvim_buf_get_lines(buf, first - 1, last, true)
  local encoded = vim.json.encode(lines)
  vim.api.nvim_buf_set_lines(buf, first - 1, last, true, { encoded })
end

---@param arg_lead string
---@return string[]
function M.complete_filter(arg_lead)
  local ok, cfg = pcall(config.get)
  if not ok then
    return {}
  end
  return util.prefix_matches(cfg.filters, arg_lead)
end

---Pipe `buf` through `argv` asynchronously. The result is applied only if
---the buffer still exists, is unchanged, and no newer request superseded it.
---@param buf integer buffer handle (not 0: callers resolve it at request)
---@param argv string[]
---@param on_done? fun(outcome: string)
function M.filter(buf, argv, on_done)
  local cfg = config.get()
  ensure_autocmds()
  M.forget(buf) -- cancel an older request for the same buffer
  local req = {} ---@type lineup.Request
  local tick = vim.api.nvim_buf_get_changedtick(buf)
  local input = vim.api.nvim_buf_get_lines(buf, 0, -1, true)

  local function finish(outcome)
    record(table.concat(argv, " ") .. ": " .. outcome)
    if on_done then
      on_done(outcome)
    end
  end

  local ok, proc = pcall(vim.system, argv, {
    stdin = input,
    text = true,
    timeout = cfg.timeout_ms,
  }, vim.schedule_wrap(function(out)
    if pending[buf] ~= req then
      return finish("cancelled")
    end
    pending[buf] = nil
    if out.code ~= 0 then
      notify(("%s exited %d: %s"):format(argv[1], out.code, out.stderr),
        vim.log.levels.ERROR)
      return finish("failed")
    end
    if not vim.api.nvim_buf_is_valid(buf)
      or vim.api.nvim_buf_get_changedtick(buf) ~= tick then
      return finish("stale")
    end
    if not vim.bo[buf].modifiable then
      notify("buffer is not modifiable", vim.log.levels.WARN)
      return finish("nomodifiable")
    end
    vim.api.nvim_buf_set_lines(buf, 0, -1, true, util.split_lines(out.stdout))
    finish("applied")
  end))
  if not ok then
    notify(tostring(proc), vim.log.levels.ERROR)
    return finish("not started")
  end
  req.proc = proc
  pending[buf] = req
end

---Command entry point: user-facing errors become notifications.
---@param fargs string[]
function M.filter_command(fargs)
  local ok, err = pcall(M.filter, vim.api.nvim_get_current_buf(), fargs)
  if not ok then
    notify(tostring(err), vim.log.levels.ERROR)
  end
end

---Show the run log in a scratch buffer owned by lineup.
function M.open_log()
  if not (log_buf and vim.api.nvim_buf_is_valid(log_buf)) then
    log_buf = vim.api.nvim_create_buf(false, true)
    vim.bo[log_buf].undolevels = -1
  end
  vim.bo[log_buf].modifiable = true
  vim.api.nvim_buf_set_lines(log_buf, 0, -1, true, log)
  vim.bo[log_buf].modifiable = false
  vim.api.nvim_open_win(log_buf, true, { split = "below", height = 8 })
  -- Set last so FileType handlers (ftplugin, user autocmds) can override.
  vim.bo[log_buf].filetype = "lineuplog"
end

M.setup = config.setup

return M
