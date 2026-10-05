---
name: gradle-build-speed
description: Helps with builds.
---

# Gradle build speed

Make Gradle builds faster without changing what they produce.

## Workflow

1. Measure first: `./gradlew build --scan` or `--profile`, and note the
   configuration and execution times separately.
1. Turn on the build cache (`org.gradle.caching=true`) and the
   configuration cache (`org.gradle.configuration-cache=true`) in
   `gradle.properties`, then fix the tasks that are not cacheable.
1. Check for tasks that run on every build because their inputs are not
   declared, and declare them.
1. Enable parallel execution (`org.gradle.parallel=true`) when projects
   are decoupled.
1. Re-measure the same command and report both times.

## Rules

- Do not raise the JVM heap before measuring garbage collection time.
- Do not disable tests to make the build faster.
