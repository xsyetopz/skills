# Bundled resource catalog

Use this catalog to locate the exact skill-local files needed for the task. Do
not load every source file into context by default. Preserve complete native
project directories—including manifests, locks, descriptors, and fixtures—when
copying or executing an example.

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
