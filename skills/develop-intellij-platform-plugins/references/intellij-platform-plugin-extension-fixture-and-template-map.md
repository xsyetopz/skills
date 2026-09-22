# Extension fixture and template map for Intellij Platform Plugin

Use this map to locate resources for IntelliJ Platform plugin. Load only the
item required by the current decision. When an example is a native project,
preserve its manifest, lockfile, descriptors, fixtures, and relative layout.

| Path | Role and evidence boundary |
| --- | --- |
| `assets/plugin-template/.gitignore` | Skill-local output material or executable fixture; use only with its documented consumer. |
| `assets/plugin-template/TEMPLATE.md` | Output template; copy and adapt without treating placeholders as facts. |
| `assets/plugin-template/build.gradle.kts` | Native project/build manifest; preserve with the adjacent example project. |
| `assets/plugin-template/gradle.properties` | Native project configuration |
| `assets/plugin-template/settings.gradle.kts` | Kotlin script or Gradle configuration |
| `assets/plugin-template/src/main/kotlin/com/example/plugin/EncodeFormValueAction.kt` | Kotlin implementation or fixture |
| `assets/plugin-template/src/main/resources/META-INF/plugin.xml` | Native manifest, descriptor, or structured fixture |
| `assets/plugin-template/src/test/kotlin/com/example/plugin/EncodeFormValueActionTest.kt` | Executable test or fault-discrimination fixture; run with the neighboring project configuration. |

## Use rules

- Use a script only for its documented IntelliJ Platform plugin transformation.
  Inspect arguments, stdout, stderr, exit status, and created files.
- Assets contain IntelliJ Platform plugin templates, fixtures, or complete
  example projects. Preserve required manifests and relative paths when copying
  them.
- A deliberately faulty fixture demonstrates fault discrimination; it is not a
  production recommendation.
- A passing bundled example establishes only its own contract in the executed
  environment; it does not prove the target system.
