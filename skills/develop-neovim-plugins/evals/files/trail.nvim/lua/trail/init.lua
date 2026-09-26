-- Highlights and strips trailing whitespace.
local M = {}

local defaults = {
  timeout = 200, -- ms to wait after the last change before highlighting
  filetypes = { 'lua', 'python', 'markdown' },
  strip_on_save = false,
}

M.config = vim.deepcopy(defaults)

local ns = vim.api.nvim_create_namespace('trail')

function M.highlight(buf)
  vim.api.nvim_buf_clear_namespace(buf, ns, 0, -1)
  for i, line in ipairs(vim.api.nvim_buf_get_lines(buf, 0, -1, false)) do
    local s = line:find('%s+$')
    if s then
      vim.api.nvim_buf_set_extmark(buf, ns, i - 1, s - 1, { end_col = #line, hl_group = 'Error' })
    end
  end
end

function M.strip(buf)
  local lines = vim.api.nvim_buf_get_lines(buf, 0, -1, false)
  for i, line in ipairs(lines) do
    lines[i] = line:gsub('%s+$', '')
  end
  vim.api.nvim_buf_set_lines(buf, 0, -1, false, lines)
end

function M.setup(opts)
  M.config = vim.tbl_extend('force', defaults, opts or {})

  vim.api.nvim_create_user_command('TrailStrip', function()
    M.strip(vim.api.nvim_get_current_buf())
  end, {})

  vim.api.nvim_create_autocmd({ 'TextChanged', 'InsertLeave' }, {
    callback = function(a)
      if vim.tbl_contains(M.config.filetypes, vim.bo[a.buf].filetype) then
        vim.defer_fn(function()
          M.highlight(a.buf)
        end, M.config.timeout)
      end
    end,
  })

  if M.config.strip_on_save then
    vim.api.nvim_create_autocmd('BufWritePre', {
      callback = function(a)
        M.strip(a.buf)
      end,
    })
  end
end

return M
