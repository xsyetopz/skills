import org.jetbrains.intellij.platform.gradle.TestFrameworkType

plugins {
    id("java")
    // Kotlin 2.4.0 is the stdlib bundled with IntelliJ Platform 2026.2.
    id("org.jetbrains.kotlin.jvm") version "2.4.0"
    id("org.jetbrains.intellij.platform") version "2.19.0"
}

group = providers.gradleProperty("group").get()
version = providers.gradleProperty("version").get()

repositories {
    mavenCentral()
    intellijPlatform {
        defaultRepositories()
    }
}

val localIde = providers.gradleProperty("platformLocalPath")

dependencies {
    intellijPlatform {
        if (localIde.isPresent) {
            local(localIde)
        } else {
            intellijIdea(providers.gradleProperty("platformVersion"))
        }
        // Optional dependency: compiled against, declared optional in
        // plugin.xml, used only from word-stats-withJson.xml classes.
        bundledPlugin("com.intellij.modules.json")
        testFramework(TestFrameworkType.Platform)
    }
    testImplementation("junit:junit:4.13.2")
    // Missing from the platform test framework (IJPL-157292).
    testImplementation("org.opentest4j:opentest4j:1.3.0")
}

kotlin {
    jvmToolchain(25)
}

intellijPlatform {
    pluginConfiguration {
        version = providers.gradleProperty("version")
        ideaVersion {
            sinceBuild = providers.gradleProperty("pluginSinceBuild")
        }
    }
    pluginVerification {
        ides {
            // Without an explicit list, recommended() downloads several IDEs.
            current()
        }
    }
    // signing {} defaults: PRIVATE_KEY, PRIVATE_KEY_PASSWORD, and
    // CERTIFICATE_CHAIN environment variables; publishing {} defaults to
    // the PUBLISH_TOKEN environment variable. Never commit either.
}

// Unified IntelliJ IDEA 2025.3+ (IU) downloads include the licensed
// com.intellij.modules.ultimate module. Without a subscription key, every
// light test failed here with "Cannot create extension ...
// [Plugin: com.intellij.modules.ultimate]". disabledPlugins is documented
// as an internal PrepareSandboxTask field; it is the knob for `test`.
tasks.prepareTestSandbox {
    disabledPlugins.add("com.intellij.modules.ultimate")
}
