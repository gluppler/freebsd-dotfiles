-- One upstream client, with explicit native servers; never install from the editor.
local M = {}
local function load()
  if not vis.communicate then return nil, 'vis 0.9+ with Lua/communicate is required.' end
  local ok, json = pcall(require, 'dkjson')
  if not ok then return nil, 'dkjson is missing; run the native build/install.' end
  -- Avoid the upstream fallback JSON encoder, which does not support UTF-8.
  package.loaded.json = json
  local loaded, client = pcall(require, 'plugins/vis-lspc')
  if not loaded then return nil, tostring(client) end
  return client
end

M.client, M.error = load()
if M.client then
  local lsp = M.client
  lsp.autostart = true
  lsp.logging = false
  lsp.menu_cmd = 'fzf'
  lsp.confirm_cmd = 'vis-menu'
  lsp.autoconfirm_edits = false
  lsp.universal_root_globs = {'.git'}
  lsp.fallback_dirname_as_root = true
  lsp.highlight_diagnostics = 'line'
  lsp.diagnostic_styles = {
    error = 'fore:black,back:white,bold', warning = 'fore:white,underlined',
    information = 'fore:white', hint = 'fore:brightblack',
  }
  local clangd = {
    name = 'clangd', cmd = 'nostromo-tool clangd --background-index --clang-tidy --header-insertion=never',
    roots = {'compile_commands.json', '.clangd', 'CMakeLists.txt', 'Makefile'},
  }
  local shell = {
    name = 'efm', cmd = 'efm-langserver',
    init_options = {documentFormatting = true},
  }
  local assembly = {name = 'asm-lsp', cmd = 'asm-lsp', roots = {'.asm-lsp.toml', 'compile_commands.json'}}
  lsp.ls_map = {
    c = clangd, ansi_c = clangd, cpp = clangd,
    rust = {name = 'rust-analyzer', cmd = 'rust-analyzer', roots = {'Cargo.toml'},
      settings = {['rust-analyzer'] = {check = {command = 'clippy'}, cargo = {allFeatures = false}}}},
    go = {name = 'gopls', cmd = 'gopls', roots = {'go.work', 'go.mod'},
      settings = {gopls = {gofumpt = false, staticcheck = true}}},
    python = {name = 'pylsp', cmd = 'pylsp', roots = {'pyproject.toml', 'uv.lock', 'setup.py'},
      settings = {pylsp = {plugins = {
        ruff = {enabled = true}, pycodestyle = {enabled = false},
        pyflakes = {enabled = false}, mccabe = {enabled = false},
        jedi_completion = {include_params = false},
      }}}},
    bash = shell, sh = shell, asm = assembly, nasm = assembly,
  }
end

function M.command(name)
  return function()
    if not M.client then vis:info('LSP unavailable: ' .. M.error); return end
    vis:command('lspc-' .. name)
  end
end

function M.rename()
  if not M.client then vis:info('LSP unavailable: ' .. M.error); return end
  vis:feedkeys(':lspc-rename ')
end

return M
