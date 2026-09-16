package __PACKAGE__

import com.intellij.openapi.actionSystem.DataContext
import com.intellij.openapi.editor.Caret
import com.intellij.openapi.editor.Editor
import com.intellij.openapi.editor.actionSystem.EditorAction
import com.intellij.openapi.editor.actionSystem.EditorWriteActionHandler
import java.net.URLEncoder
import java.nio.charset.StandardCharsets

class EncodeFormValueAction : EditorAction(Handler()) {
    private class Handler : EditorWriteActionHandler.ForEachCaret() {
        override fun isEnabledForCaret(
            editor: Editor,
            caret: Caret,
            dataContext: DataContext,
        ): Boolean = caret.hasSelection()

        override fun executeWriteAction(editor: Editor, caret: Caret, dataContext: DataContext) {
            val selected = caret.selectedText ?: return
            val start = caret.selectionStart
            val encoded = URLEncoder.encode(selected, StandardCharsets.UTF_8)
            editor.document.replaceString(start, caret.selectionEnd, encoded)
            caret.setSelection(start, start + encoded.length)
        }
    }
}
