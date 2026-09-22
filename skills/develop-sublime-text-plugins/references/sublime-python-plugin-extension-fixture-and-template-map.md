# Extension fixture and template map for Sublime Python Plugin

Use this map to locate resources for Sublime Text plugin. Load only the item
required by the current decision. When an example is a native project, preserve
its manifest, lockfile, descriptors, fixtures, and relative layout.

| Path | Role and evidence boundary |
| --- | --- |
| `assets/package-template/.python-version` | Skill-local output material or executable fixture; use only with its documented consumer. |
| `assets/package-template/Default.sublime-commands` | Deliberately defective fixture used to prove the check rejects a relevant fault; never copy into production. |
| `assets/package-template/ExamplePlugin.py` | Python implementation, test, or deterministic helper |
| `assets/package-template/TEMPLATE.md` | Output template; copy and adapt without treating placeholders as facts. |
| `assets/package-template/tests/test_commands.py` | Executable test or fault-discrimination fixture; run with the neighboring project configuration. |
| `assets/type-stubs/sublime.pyi` | Skill-local output material or executable fixture; use only with its documented consumer. |
| `assets/type-stubs/sublime_plugin.pyi` | Skill-local output material or executable fixture; use only with its documented consumer. |

## Use rules

- Use a script only for its documented Sublime Text plugin transformation.
  Inspect arguments, stdout, stderr, exit status, and created files.
- Assets contain Sublime Text plugin templates, fixtures, or complete example
  projects. Preserve required manifests and relative paths when copying them.
- A deliberately faulty fixture demonstrates fault discrimination; it is not a
  production recommendation.
- A passing bundled example establishes only its own contract in the executed
  environment; it does not prove the target system.
