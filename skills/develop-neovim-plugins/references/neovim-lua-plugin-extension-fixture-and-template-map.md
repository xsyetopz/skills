# Extension fixture and template map for Neovim Lua Plugin

Use this map to locate resources for Neovim plugin. Load only the item required
by the current decision. When an example is a native project, preserve its
manifest, lockfile, descriptors, fixtures, and relative layout.

| Path | Role and evidence boundary |
| --- | --- |
| `assets/plugin-template/TEMPLATE.md` | Output template; copy and adapt without treating placeholders as facts. |
| `assets/plugin-template/doc/example.txt` | Text fixture or native metadata |
| `assets/plugin-template/lua/example/init.lua` | Lua implementation or fixture |
| `assets/plugin-template/plugin/example.lua` | Lua implementation or fixture |
| `assets/plugin-template/tests/minimal_init.lua` | Executable test or fault-discrimination fixture; run with the neighboring project configuration. |
| `assets/plugin-template/tests/smoke.lua` | Executable test or fault-discrimination fixture; run with the neighboring project configuration. |

## Use rules

- Use a script only for its documented Neovim plugin transformation. Inspect
  arguments, stdout, stderr, exit status, and created files.
- Assets contain Neovim plugin templates, fixtures, or complete example
  projects. Preserve required manifests and relative paths when copying them.
- A deliberately faulty fixture demonstrates fault discrimination; it is not a
  production recommendation.
- A passing bundled example establishes only its own contract in the executed
  environment; it does not prove the target system.
