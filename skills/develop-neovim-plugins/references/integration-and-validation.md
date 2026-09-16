# Test and distribute Neovim editor plugins

## Use existing editor integrations

For LSP, use the host APIs supported by the declared minimum: on newer hosts,
`vim.lsp.config` defines configuration and `vim.lsp.enable` enables activation.
Do not copy that API into a plugin targeting an older host. Specify the server
command, filetypes, and root behavior; reuse a suitable workspace client rather
than starting a process for every buffer. Inspect the actual client and server
capabilities instead of assuming every advertised LSP operation is supported.
See [LSP help][ref-lsp-help].

Use an owned diagnostic namespace and `vim.diagnostic.set/reset` for diagnostic
data, not a custom sign/virtual-text framework that reproduces it. Preserve
other clients' results and honor user display configuration. A diagnostic's
source positions still need the correct buffer/encoding conversion.

Add `lua/<name>/health.lua` only for prerequisites or conditions a user can act
on. Its `check()` function can use `vim.health.start/ok/warn/error`. Keep it
read-only and give a concrete resolution. Do not emit fake warnings for an
optional executable that the plugin does not actually use. See [health
help][source-2].

## Real-host tests

Use a copied package and temporary XDG config/data/state/cache directories, plus
an explicit runtimepath. `--clean` excludes normal user initialization and
ShaDa; an explicit minimal init adds only the package under test. Read the
installed [startup help][source-3] for the target version rather than inventing
flags.

The [starter](../assets/plugin-template/TEMPLATE.md) runs its Lua script through
`-l`, which exits nonzero on an unhandled Lua error. Keep expected-failure
checks explicit; do not catch all failures and exit with `qa!` regardless of
outcome. The sample uses the real editor API and ordinary Lua assertions. A
larger suite should reuse the repository's existing runner, not grow this smoke
script into a bespoke framework.

Exercise behavior, not just command existence: actual buffer contents, intended
range boundaries, undo/redo, buffer options, repeated loading, and help lookup.
Use a fault that would violate the contract to check that tests detect it. Do
not replace `vim` with a mock for claims about the real editor.

For asynchronous features, drive the ordering explicitly: request, buffer
change/switch/close, then completion. `vim.wait` can wait for a test condition
with a deadline; a fixed sleep is not evidence of completion. Test cancellation
and stale output separately from a successful subprocess. Use the real process
boundary where exit status, output chunking, or argument escaping matters.

Run the minimum supported version and a current stable host. Report exact
versions and distinguish headless tests from interactive UI checks. Screenshots
are useful for rendered behavior, not a substitute for assertions about data or
resource cleanup. `:messages`, `:scriptnames`, and `:verbose command Name` can
diagnose registration; inspect the plugin's actual augroups rather than
inventing a diagnostic command the plugin does not expose.

## Help and installation

Help files use unique tags such as `*example.nvim*` and `*:ExampleJsonLines*`.
Run `:helptags` in the copied package, then resolve the advertised topic with
`:help`. Generating a tags file alone does not prove that its target resolves.
Do not commit generated help tags or test caches. See [help
authoring][source-1].

Inspect repository/archive layout: `plugin/`, `lua/`, `doc/`, and required
assets must be at the installed runtimepath root. Test the artifact through a
clean runtimepath, not through a source checkout that masks missing files.
Package managers have their own installation conventions; no universal Neovim
manifest or arbitrary schema-version field is required.

Document the supported host, actual dependencies, public commands, defaults, and
side effects. Do not add setup, keymaps, LSP configuration, or health checks
just to fill a template. A command-only example should remain command-only.
Publication or modification of a hosted plugin registry is a separate authorized
action; a local archive test does not prove publication.

[source-1]: https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/helphelp.txt
[source-2]: https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/health.txt
[source-3]: https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/starting.txt

[ref-lsp-help]: https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/lsp.txt
