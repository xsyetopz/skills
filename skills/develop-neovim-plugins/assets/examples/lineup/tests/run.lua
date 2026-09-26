-- Self-contained headless suite for lineup. From the plugin root:
--   nvim --clean --headless -u tests/minimal_init.lua -l tests/run.lua
-- Prints "ok <name>" or "FAIL <name>: <reason>" per test; exits 1 on any
-- failure. Uses the real editor API and real processes; no mocks of `vim`.
local api = vim.api
local tests, failed = {}, {}

local function test(name, fn)
  tests[#tests + 1] = { name = name, fn = fn }
end

local function eq(actual, expected, what)
  if not vim.deep_equal(actual, expected) then
    error(("%s: expected %s, got %s"):format(what, vim.inspect(expected),
      vim.inspect(actual)), 2)
  end
end

---Fresh scratch-free buffer with `lines`, undo block closed.
local function buffer(lines)
  vim.cmd.enew({ bang = true })
  api.nvim_buf_set_lines(0, 0, -1, true, lines)
  vim.o.undolevels = vim.o.undolevels -- close the fixture's undo block
  return api.nvim_get_current_buf()
end

local function lines(buf)
  return api.nvim_buf_get_lines(buf or 0, 0, -1, true)
end

---Run lineup.filter and wait for its outcome (real process, real loop).
local function filter_and_wait(buf, argv, before_wait)
  local outcome
  require("lineup").filter(buf, argv, function(o)
    outcome = o
  end)
  if before_wait then
    before_wait()
  end
  assert(vim.wait(5000, function()
    return outcome ~= nil
  end, 10), "filter did not finish within 5000 ms")
  return outcome
end

---Capture vim.notify calls while `fn` runs.
local function capture_notify(fn)
  local seen, original = {}, vim.notify
  vim.notify = function(msg, level)
    seen[#seen + 1] = { msg = msg, level = level }
  end
  local ok, err = pcall(fn)
  vim.notify = original
  assert(ok, err)
  return seen
end

test("lazy startup: commands and maps exist, lineup not loaded", function()
  eq(package.loaded["lineup"], nil, "package.loaded.lineup")
  local cmds = api.nvim_get_commands({})
  for _, name in ipairs({ "LineupJson", "LineupFilter", "LineupLog" }) do
    assert(cmds[name], name .. " missing")
  end
  eq(cmds.LineupFilter.nargs, "+", "LineupFilter nargs")
  assert(vim.fn.maparg("<Plug>(LineupJson)", "n") ~= "", "n <Plug> map")
  assert(vim.fn.maparg("<Plug>(LineupJson)", "x") ~= "", "x <Plug> map")
end)

test("no default mappings outside <Plug>", function()
  for _, mode in ipairs({ "n", "x", "i", "o" }) do
    for _, map in ipairs(api.nvim_get_keymap(mode)) do
      if (map.desc or ""):find("^lineup:") then
        assert(map.lhs:find("^<Plug>"), "default map " .. map.lhs)
      end
    end
  end
end)

test("json encodes the range and leaves other lines", function()
  buffer({ "before", 'a"b', "c\\d", "café 雪", "", "after" })
  vim.cmd("2,5LineupJson")
  eq(lines(), { "before", '["a\\"b","c\\\\d","café 雪",""]', "after" },
    "buffer")
end)

test("json is one undo step", function()
  buffer({ "x", "y", "z" })
  local before = vim.fn.undotree().seq_last
  vim.cmd("%LineupJson")
  eq(vim.fn.undotree().seq_last - before, 1, "undo sequence delta")
  vim.cmd("silent undo")
  eq(lines(), { "x", "y", "z" }, "after undo")
end)

test("json respects nomodifiable, not readonly", function()
  local buf = buffer({ "keep" })
  vim.bo[buf].modifiable = false
  local ok, err = pcall(vim.cmd, "LineupJson")
  assert(not ok and tostring(err):find("Buffer is not 'modifiable'", 1, true),
    tostring(err))
  eq(lines(), { "keep" }, "nomodifiable buffer")
  vim.bo[buf].modifiable = true
  vim.bo[buf].readonly = true
  vim.cmd("LineupJson")
  eq(lines(), { '["keep"]' }, "readonly buffer")
end)

test("<Plug> mapping works in visual mode through a user map", function()
  vim.keymap.set("x", "<Leader>j", "<Plug>(LineupJson)")
  buffer({ "a", "b", "c" })
  vim.cmd("normal " .. vim.keycode("Vj<Leader>j"))
  eq(lines(), { '["a","b"]', "c" }, "visual selection")
  vim.keymap.del("x", "<Leader>j")
end)

test("user command nargs and completion", function()
  local ok, err = pcall(vim.cmd, "LineupFilter")
  assert(not ok and tostring(err):find("E471"), tostring(err))
  eq(vim.fn.getcompletion("LineupFilter s", "cmdline"), { "sort" },
    "completion")
  eq(vim.fn.getcompletion("LineupFilter sort -", "cmdline"), {},
    "no completion after program")
end)

test("filter applies output to an unchanged buffer", function()
  local buf = buffer({ "b", "a", "c" })
  eq(filter_and_wait(buf, { "sort" }), "applied", "outcome")
  eq(lines(buf), { "a", "b", "c" }, "sorted")
end)

test("filter discards a stale result", function()
  local buf = buffer({ "b", "a" })
  local outcome = filter_and_wait(buf, { "sh", "-c", "sleep 0.2; sort" },
    function()
      api.nvim_buf_set_lines(buf, 0, 0, true, { "typed" })
    end)
  eq(outcome, "stale", "outcome")
  eq(lines(buf), { "typed", "b", "a" }, "user edit kept")
end)

test("filter edits the initiating buffer, not the current one", function()
  local a = buffer({ "2", "1" })
  local b
  local outcome = filter_and_wait(a, { "sh", "-c", "sleep 0.2; sort" },
    function()
      b = buffer({ "other" })
    end)
  eq(outcome, "applied", "outcome")
  eq(lines(a), { "1", "2" }, "initiating buffer")
  eq(lines(b), { "other" }, "current buffer")
end)

test("a newer request cancels the older one", function()
  local buf = buffer({ "b", "a" })
  local first
  require("lineup").filter(buf, { "sh", "-c", "sleep 0.3; cat" },
    function(o)
      first = o
    end)
  eq(filter_and_wait(buf, { "sort" }), "applied", "second")
  assert(vim.wait(2000, function()
    return first ~= nil
  end, 10), "first never finished")
  eq(first, "cancelled", "first")
  eq(lines(buf), { "a", "b" }, "buffer")
end)

test("wiping the buffer kills the process", function()
  local buf = buffer({ "x" })
  local start = vim.uv.hrtime()
  local outcome = filter_and_wait(buf, { "sleep", "5" }, function()
    api.nvim_buf_delete(buf, { force = true })
  end)
  eq(outcome, "cancelled", "outcome")
  local ms = (vim.uv.hrtime() - start) / 1e6
  assert(ms < 2000, ("process outlived wipeout: %d ms"):format(ms))
end)

test("nonzero exit notifies and keeps the buffer", function()
  local buf = buffer({ "keep" })
  local outcome
  local seen = capture_notify(function()
    outcome = filter_and_wait(buf, { "sh", "-c", "echo bad >&2; exit 3" })
  end)
  eq(outcome, "failed", "outcome")
  eq(lines(buf), { "keep" }, "buffer")
  eq(#seen, 1, "notifications")
  eq(seen[1].level, vim.log.levels.ERROR, "level")
  eq(seen[1].msg, "lineup: sh exited 3: bad\n", "message")
end)

test("a program that cannot start notifies instead of raising", function()
  buffer({ "keep" })
  local seen = capture_notify(function()
    vim.cmd("LineupFilter lineup-no-such-program")
  end)
  eq(#seen, 1, "notifications")
  assert(seen[1].msg:find("lineup-no-such-program", 1, true), seen[1].msg)
  print("  start failure message: " .. seen[1].msg)
end)

test("autocmd group holds one handler after repeated runs", function()
  local buf = buffer({ "1" })
  for _ = 1, 3 do
    filter_and_wait(buf, { "cat" })
  end
  eq(#api.nvim_get_autocmds({ group = "lineup" }), 1, "autocmds")
end)

test("uv callbacks need vim.schedule for editor API (E5560)", function()
  local direct, scheduled
  local timer = assert(vim.uv.new_timer())
  timer:start(0, 0, function()
    local ok, err = pcall(api.nvim_get_current_line)
    direct = ok and "no error" or err
    vim.schedule(function()
      scheduled = api.nvim_get_current_line()
    end)
    timer:close()
  end)
  assert(vim.wait(1000, function()
    return scheduled ~= nil
  end, 10), "scheduled callback never ran")
  assert(direct:find("E5560", 1, true), direct)
  print("  direct call error: " .. direct)
end)

test("config: vim.g read at use, setup wins, bad values notify", function()
  local config = require("lineup.config")
  vim.g.lineup = { filters = { "uniq" }, typo = true }
  local cfg, unknown = config.get()
  eq(cfg.filters, { "uniq" }, "vim.g filters")
  eq(unknown, { "typo" }, "unknown keys")
  require("lineup").setup({ timeout_ms = 10 })
  eq(config.get().timeout_ms, 10, "setup override")
  vim.g.lineup = { timeout_ms = "soon" }
  require("lineup").setup(nil)
  local seen = capture_notify(function()
    vim.cmd("LineupFilter sort")
  end)
  eq(#seen, 1, "notifications")
  assert(seen[1].msg:find("timeout_ms: expected positive integer, got soon",
    1, true), seen[1].msg)
  local ok, err = pcall(require("lineup").setup, "x")
  assert(not ok and err:find("opts: expected table, got string", 1, true),
    tostring(err))
  vim.g.lineup = nil
end)

test("checkhealth reports config and filters", function()
  vim.g.lineup = { filters = { "sort", "lineup-missing" }, typo = 1 }
  vim.cmd("silent checkhealth lineup")
  local text = table.concat(lines(), "\n")
  vim.cmd("bwipeout!")
  vim.g.lineup = nil
  for _, want in ipairs({ "OK configuration is valid",
    "WARNING unknown option: typo", "OK filter `sort` found",
    "WARNING filter `lineup-missing` is not executable" }) do
    assert(text:find(want, 1, true), "missing: " .. want .. "\n" .. text)
  end
end)

test("ftplugin: local options and map, undone on filetype change",
  function()
  buffer({ "main" })
  local main_win = api.nvim_get_current_win()
  require("lineup").open_log()
  local log_buf = api.nvim_get_current_buf()
  local log_win = api.nvim_get_current_win()
  eq(vim.bo[log_buf].filetype, "lineuplog", "filetype")
  eq(vim.wo[log_win].wrap, false, "log window wrap")
  eq(vim.wo[main_win].wrap, true, "main window wrap")
  eq(vim.fn.maparg("q", "n", false, true).buffer, 1, "buffer-local q")
  vim.bo[log_buf].filetype = "text"
  eq(vim.fn.maparg("q", "n"), "", "q after filetype change")
  eq(vim.wo[log_win].wrap, true, "wrap after filetype change")
  api.nvim_win_close(log_win, true)
end)

test("help tags resolve", function()
  local root = vim.fn.fnamemodify(debug.getinfo(1, "S").source:sub(2),
    ":p:h:h")
  vim.cmd.helptags(vim.fn.fnameescape(root .. "/doc"))
  for _, topic in ipairs({ "lineup", ":LineupFilter", "<Plug>(LineupJson)",
    "g:lineup" }) do
    vim.cmd.help(topic)
    eq(vim.bo.filetype, "help", "help " .. topic)
    vim.cmd.helpclose()
  end
end)

test("re-sourcing plugin/ is idempotent", function()
  vim.cmd("runtime! plugin/lineup.lua")
  vim.g.loaded_lineup = nil
  vim.cmd("runtime! plugin/lineup.lua")
  local n = 0
  for _, map in ipairs(api.nvim_get_keymap("n")) do
    if map.lhs == "<Plug>(LineupJson)" then
      n = n + 1
    end
  end
  eq(n, 1, "normal <Plug> maps")
  buffer({ "still works" })
  vim.cmd("LineupJson")
  eq(lines(), { '["still works"]' }, "command after reload")
end)

for _, t in ipairs(tests) do
  local ok, err = pcall(t.fn)
  if ok then
    print("ok   " .. t.name)
  else
    failed[#failed + 1] = t.name
    print("FAIL " .. t.name .. ": " .. tostring(err))
  end
end
print("")
print("failed: " .. table.concat(failed, " | "))
print(("%d passed, %d failed (%s)"):format(#tests - #failed, #failed,
  tostring(vim.version())))
if #failed > 0 then
  os.exit(1)
end
