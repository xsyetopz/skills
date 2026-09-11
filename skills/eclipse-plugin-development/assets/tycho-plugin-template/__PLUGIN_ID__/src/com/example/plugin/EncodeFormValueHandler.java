package __JAVA_PACKAGE__;

import org.eclipse.core.commands.AbstractHandler;
import org.eclipse.core.commands.ExecutionEvent;
import org.eclipse.core.commands.ExecutionException;
import org.eclipse.jface.text.BadLocationException;
import org.eclipse.jface.text.IBlockTextSelection;
import org.eclipse.jface.text.IMultiTextSelection;
import org.eclipse.jface.text.ITextSelection;
import org.eclipse.ui.handlers.HandlerUtil;
import org.eclipse.ui.texteditor.ITextEditor;
import org.eclipse.ui.texteditor.ITextEditorExtension2;

import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;

public final class EncodeFormValueHandler extends AbstractHandler {
    @Override
    public Object execute(ExecutionEvent event) throws ExecutionException {
        if (!(HandlerUtil.getActiveEditor(event) instanceof ITextEditor editor)) {
            return null;
        }
        if (editor instanceof ITextEditorExtension2 extended) {
            if (!extended.validateEditorInputState()) {
                return null;
            }
        } else if (!editor.isEditable()) {
            return null;
        }
        if (!(editor.getSelectionProvider().getSelection() instanceof ITextSelection selection)
                || selection.getLength() <= 0) {
            return null;
        }
        if (selection instanceof IBlockTextSelection
                || selection instanceof IMultiTextSelection multi
                        && multi.getRegions().length != 1) {
            throw new ExecutionException(
                    "Select one continuous text range, not a block or multiple ranges.");
        }
        var document = editor.getDocumentProvider().getDocument(editor.getEditorInput());
        try {
            var encoded =
                    URLEncoder.encode(
                            document.get(selection.getOffset(), selection.getLength()),
                            StandardCharsets.UTF_8);
            document.replace(selection.getOffset(), selection.getLength(), encoded);
            editor.selectAndReveal(selection.getOffset(), encoded.length());
        } catch (BadLocationException exception) {
            throw new ExecutionException("The selected text could not be encoded.", exception);
        }
        return null;
    }
}
