# Extension fixture and template map for Eclipse OSGi Plugin

Use this map to locate resources for Eclipse plugin. Load only the item required
by the current decision. When an example is a native project, preserve its
manifest, lockfile, descriptors, fixtures, and relative layout.

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

- Use a script only for its documented Eclipse plugin transformation. Inspect
  arguments, stdout, stderr, exit status, and created files.
- Assets contain Eclipse plugin templates, fixtures, or complete example
  projects. Preserve required manifests and relative paths when copying them.
- A deliberately faulty fixture demonstrates fault discrimination; it is not a
  production recommendation.
- A passing bundled example establishes only its own contract in the executed
  environment; it does not prove the target system.
