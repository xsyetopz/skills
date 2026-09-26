package org.acme.wordstats

import com.intellij.notification.Notification
import com.intellij.notification.NotificationType
import com.intellij.notification.Notifications
import com.intellij.openapi.components.service
import com.intellij.testFramework.PlatformTestUtil
import com.intellij.testFramework.common.timeoutRunBlocking
import com.intellij.testFramework.fixtures.BasePlatformTestCase

class NotificationAndActionTest : BasePlatformTestCase() {
    private val shown = mutableListOf<Notification>()

    override fun setUp() {
        super.setUp()
        // notify(project) publishes on the project bus, not the app bus.
        project.messageBus
            .connect(testRootDisposable)
            .subscribe(Notifications.TOPIC, object : Notifications {
                override fun notify(notification: Notification) {
                    shown += notification
                }
            })
    }

    fun testBalloonGroupNotification() {
        NotificationReporter(project).report("a.txt", 3)
        val notification = shown.single()
        assertEquals("Word Stats", notification.groupId)
        assertEquals("a.txt: 3 words", notification.content)
        assertEquals(NotificationType.INFORMATION, notification.type)
    }

    fun testZeroCountBecomesStickySuggestion() {
        NotificationReporter(project).report("a.txt", 0)
        val notification = shown.single()
        assertEquals("Word Stats Suggestions", notification.groupId)
        assertTrue(notification.isSuggestionType)
        assertEquals(1, notification.actions.size)
    }

    fun testOptionalDependencyRegisteredJsonFilter() {
        val filters = wordFilters().map { it.javaClass.simpleName }
        assertContainsElements(filters, "JsonLiteralFilter")
    }

    fun testWriteBlockingReadReturnsLength() {
        val file = myFixture.configureByText("notes.txt", "12345")
        val length = timeoutRunBlocking {
            project.service<WordStatsService>().fileLength(file.virtualFile)
        }
        assertEquals(5, length)
    }

    fun testEdtUpdateNeedsSelection() {
        myFixture.configureByText("notes.txt", "one two three")
        assertFalse(myFixture.testAction(CountSelectionAction()).isEnabled)
    }

    fun testSelectionCountRunsInActionCoroutine() {
        myFixture.configureByText("notes.txt", "<selection>one two</selection>")
        val presentation = myFixture.testAction(CountSelectionAction())
        assertTrue(presentation.isEnabled)
        val reporter = project.service<WordStatsReporter>() as RecordingReporter
        val deadline = System.nanoTime() + 10_000_000_000
        while ("selection" to 2 !in reporter.reports &&
            System.nanoTime() < deadline
        ) {
            PlatformTestUtil.dispatchAllInvocationEventsInIdeEventQueue()
        }
        assertContainsElements(reporter.reports, "selection" to 2)
    }
}
