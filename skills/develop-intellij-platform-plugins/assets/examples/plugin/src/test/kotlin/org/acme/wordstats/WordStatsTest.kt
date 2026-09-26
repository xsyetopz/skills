package org.acme.wordstats

import com.intellij.openapi.actionSystem.IdeActions
import com.intellij.openapi.application.ReadAction
import com.intellij.openapi.components.service
import com.intellij.testFramework.PlatformTestUtil
import com.intellij.testFramework.common.timeoutRunBlocking
import com.intellij.testFramework.fixtures.BasePlatformTestCase

class WordStatsTest : BasePlatformTestCase() {
    private val settings get() = service<WordStatsSettings>()

    override fun tearDown() {
        try {
            // Application-level state survives between light tests.
            settings.loadState(WordStatsSettings.State())
        } finally {
            super.tearDown()
        }
    }

    fun testCountsPlainTextWords() {
        val file = myFixture.configureByText("notes.txt", "alpha beta\ngamma")
        assertEquals(3, ReadAction.computeBlocking<Int, Throwable> {
            countPsiWords(file)
        })
    }

    fun testExtensionFilterReadsSettings() {
        settings.minLength = 5
        val file = myFixture.configureByText("notes.txt", "alpha be gamma")
        assertEquals(2, ReadAction.computeBlocking<Int, Throwable> {
            countPsiWords(file)
        })
    }

    fun testExtensionPointListsRegisteredFilters() {
        val filters = wordFilters().map { it.javaClass.simpleName }
        assertContainsElements(filters, "MinLengthFilter")
    }

    fun testServiceScopeCountsAndTestReporterRecords() {
        val file = myFixture.configureByText("notes.txt", "one two three")
        val reporter = project.service<WordStatsReporter>()
        assertInstanceOf(reporter, RecordingReporter::class.java)
        timeoutRunBlocking {
            project.service<WordStatsService>()
                .countInBackground(file.virtualFile)
                .join()
        }
        assertContainsElements(
            (reporter as RecordingReporter).reports,
            "notes.txt" to 3,
        )
        assertEquals(3, project.service<ProjectWordStats>().state.lastCount)
    }

    fun testNonBlockingReadDeliversOnEdt() {
        val file = myFixture.configureByText("notes.txt", "one two")
        var result: Int? = null
        project.service<WordStatsService>()
            .countNonBlocking(file.virtualFile) { result = it }
        val deadline = System.nanoTime() + 10_000_000_000
        while (result == null && System.nanoTime() < deadline) {
            PlatformTestUtil.dispatchAllInvocationEventsInIdeEventQueue()
        }
        assertEquals(2, result)
    }

    fun testWriteCommandIsOneUndoStep() {
        myFixture.configureByText("notes.txt", "text")
        val document = myFixture.editor.document
        project.service<WordStatsService>().appendSummaryOnEdt(document, 1)
        assertEquals("text\nwords: 1", document.text)
        myFixture.performEditorAction(IdeActions.ACTION_UNDO)
        assertEquals("text", document.text)
    }

    fun testCountWordsActionEnabledForFile() {
        myFixture.configureByText("notes.txt", "a")
        val presentation = myFixture.testAction(CountWordsAction())
        assertTrue(presentation.isEnabledAndVisible)
    }

    fun testSerializableStateTracksModifications() {
        val before = settings.stateModificationCount
        settings.minLength = 3
        assertEquals(3, settings.state.minLength)
        assertTrue(settings.stateModificationCount > before)
    }

    fun testJavaStateComponentKeepsFiveRecentFiles() {
        val log = service<LegacyRunLog>()
        log.loadState(LegacyRunLog.RunState())
        repeat(6) { log.recordRun("f$it") }
        assertEquals(6, log.state.runs)
        assertEquals(
            listOf("f5", "f4", "f3", "f2", "f1"),
            log.state.recentFiles,
        )
    }

    fun testConfigurableBindsToSettings() {
        val configurable = WordStatsConfigurable()
        try {
            configurable.createComponent()
            configurable.reset()
            assertFalse(configurable.isModified)
            settings.minLength = 7
            assertTrue(configurable.isModified)
            configurable.reset()
            assertFalse(configurable.isModified)
        } finally {
            configurable.disposeUIResources()
        }
    }
}
