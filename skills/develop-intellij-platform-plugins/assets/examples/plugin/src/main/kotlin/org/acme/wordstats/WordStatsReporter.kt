package org.acme.wordstats

import com.intellij.notification.NotificationAction
import com.intellij.notification.NotificationGroupManager
import com.intellij.notification.NotificationType
import com.intellij.openapi.components.service
import com.intellij.openapi.options.ShowSettingsUtil
import com.intellij.openapi.project.Project
import java.util.concurrent.CopyOnWriteArrayList

/** Registered (non-light) project service: API plus test replacement. */
interface WordStatsReporter {
    fun report(fileName: String, count: Int)
}

internal class NotificationReporter(
    private val project: Project,
) : WordStatsReporter {
    override fun report(fileName: String, count: Int) {
        if (count == 0) {
            suggestSettings(fileName)
            return
        }
        if (!service<WordStatsSettings>().notifyOnFinish) return
        NotificationGroupManager.getInstance()
            .getNotificationGroup("Word Stats")
            .createNotification(
                "$fileName: $count words",
                NotificationType.INFORMATION,
            )
            .notify(project)
    }

    // STICKY_BALLOON group: stays until the user acts or dismisses it.
    private fun suggestSettings(fileName: String) {
        NotificationGroupManager.getInstance()
            .getNotificationGroup("Word Stats Suggestions")
            .createNotification(
                "No words counted in $fileName",
                "The minimum word length may be too high.",
                NotificationType.WARNING,
            )
            .setSuggestionType(true)
            .addAction(
                NotificationAction.createSimpleExpiring("Open settings") {
                    ShowSettingsUtil.getInstance().showSettingsDialog(
                        project,
                        WordStatsConfigurable::class.java,
                    )
                },
            )
            .notify(project)
    }
}

/** testServiceImplementation: records reports instead of notifying. */
class RecordingReporter : WordStatsReporter {
    val reports: MutableList<Pair<String, Int>> = CopyOnWriteArrayList()

    override fun report(fileName: String, count: Int) {
        reports += fileName to count
    }
}
