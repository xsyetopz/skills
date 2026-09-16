# Bundled resource catalog

Use this catalog to locate the exact skill-local files needed for the task. Do
not load every source file into context by default. Preserve complete native
project directories—including manifests, locks, descriptors, and fixtures—when
copying or executing an example.

| Path | Role and evidence boundary |
| --- | --- |
| `assets/tycho-plugin-template/TEMPLATE.md` | Output template; copy and adapt without treating placeholders as facts. |
| `assets/tycho-plugin-template/__PLUGIN_ID__/META-INF/MANIFEST.MF` | Skill-local output material or executable fixture; use only with its documented consumer. |
| `assets/tycho-plugin-template/__PLUGIN_ID__/build.properties` | Native project configuration |
| `assets/tycho-plugin-template/__PLUGIN_ID__/plugin.xml` | Native manifest, descriptor, or structured fixture |
| `assets/tycho-plugin-template/__PLUGIN_ID__/pom.xml` | Native project/build manifest; preserve with the adjacent example project. |
| `assets/tycho-plugin-template/__PLUGIN_ID__/src/com/example/plugin/EncodeFormValueHandler.java` | Java implementation or fixture |
| `assets/tycho-plugin-template/__PLUGIN_ID__.feature/feature.xml` | Native manifest, descriptor, or structured fixture |
| `assets/tycho-plugin-template/__PLUGIN_ID__.feature/pom.xml` | Native project/build manifest; preserve with the adjacent example project. |
| `assets/tycho-plugin-template/__PLUGIN_ID__.repository/category.xml` | Native manifest, descriptor, or structured fixture |
| `assets/tycho-plugin-template/__PLUGIN_ID__.repository/pom.xml` | Native project/build manifest; preserve with the adjacent example project. |
| `assets/tycho-plugin-template/__PLUGIN_ID__.tests/META-INF/MANIFEST.MF` | Skill-local output material or executable fixture; use only with its documented consumer. |
| `assets/tycho-plugin-template/__PLUGIN_ID__.tests/build.properties` | Native project configuration |
| `assets/tycho-plugin-template/__PLUGIN_ID__.tests/pom.xml` | Native project/build manifest; preserve with the adjacent example project. |
| `assets/tycho-plugin-template/__PLUGIN_ID__.tests/src/com/example/plugin/tests/EncodeFormValueTest.java` | Executable test or fault-discrimination fixture; run with the neighboring project configuration. |
| `assets/tycho-plugin-template/pom.xml` | Native project/build manifest; preserve with the adjacent example project. |

## Use rules

- `scripts/` contains executable helpers for the skill workflow. Run a helper
  only with documented arguments and inspect stdout/stderr and exit status.
- `assets/` contains templates, complete example projects, fixtures, and other
  material copied, adapted, or executed as part of the task. Assets are not
  instructions by themselves.
- Deliberately faulty fixtures exist only to demonstrate fault discrimination.
  Never present them as recommended implementation code.
- A compiled or passing bundled example establishes only its own contract in the
  executed environment. It does not prove the target repository or production
  system correct.
