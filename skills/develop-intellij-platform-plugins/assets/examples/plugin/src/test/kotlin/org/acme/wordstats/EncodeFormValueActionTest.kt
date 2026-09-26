package org.acme.wordstats

import com.intellij.openapi.actionSystem.IdeActions
import com.intellij.openapi.editor.VisualPosition
import com.intellij.testFramework.fixtures.BasePlatformTestCase

class EncodeFormValueActionTest : BasePlatformTestCase() {
    fun testMultipleSelectionsAndSingleUndo() {
        myFixture.configureByText("values.txt", "a b+é\nx y\nuntouched")
        val editor = myFixture.editor
        editor.caretModel.primaryCaret.setSelection(0, 5)
        val second =
            requireNotNull(editor.caretModel.addCaret(VisualPosition(1, 0)))
        second.setSelection(6, 9)
        requireNotNull(editor.caretModel.addCaret(VisualPosition(2, 0)))

        myFixture.performEditorAction(ENCODE)

        assertEquals("a+b%2B%C3%A9\nx+y\nuntouched", editor.document.text)
        assertEquals(
            listOf("a+b%2B%C3%A9", "x+y", null),
            editor.caretModel.allCarets.map { it.selectedText },
        )
        myFixture.performEditorAction(IdeActions.ACTION_UNDO)
        assertEquals("a b+é\nx y\nuntouched", editor.document.text)
    }

    fun testNoSelectionDoesNotChangeDocument() {
        myFixture.configureByText("values.txt", "unchanged")
        val document = myFixture.editor.document
        val stamp = document.modificationStamp
        myFixture.performEditorAction(ENCODE)
        assertEquals("unchanged", document.text)
        assertEquals(stamp, document.modificationStamp)
    }

    private companion object {
        const val ENCODE = "org.acme.wordstats.EncodeFormValue"
    }
}
