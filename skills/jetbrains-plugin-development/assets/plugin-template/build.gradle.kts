plugins {
    id("java")
    id("org.jetbrains.kotlin.jvm") version "__KOTLIN_VERSION__"
    id("org.jetbrains.intellij.platform") version "__INTELLIJ_PLATFORM_GRADLE_PLUGIN_VERSION__"
}

group = providers.gradleProperty("group").get()
version = providers.gradleProperty("version").get()

repositories {
    mavenCentral()
    intellijPlatform {
        defaultRepositories()
    }
}

dependencies {
    intellijPlatform {
        create(
            providers.gradleProperty("platformType"),
            providers.gradleProperty("platformVersion"),
        )
        testFramework(org.jetbrains.intellij.platform.gradle.TestFrameworkType.Platform)
    }
    testImplementation("junit:junit:4.13.2")
}

kotlin {
    jvmToolchain(__JAVA_VERSION__)
}

intellijPlatform {
    pluginConfiguration {
        id = providers.gradleProperty("pluginId")
        name = providers.gradleProperty("pluginName")
        version = providers.gradleProperty("version")
        ideaVersion {
            sinceBuild = providers.gradleProperty("pluginSinceBuild")
        }
        vendor {
            name = "__VENDOR_NAME__"
        }
    }
    pluginVerification {
        ides {
            recommended()
        }
    }
}

tasks.test {
    useJUnit()
}
