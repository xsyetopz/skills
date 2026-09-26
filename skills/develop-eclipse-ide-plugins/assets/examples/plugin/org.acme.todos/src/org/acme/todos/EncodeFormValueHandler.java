package org.acme.todos;

import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;

import org.eclipse.core.commands.AbstractHandler;
import org.eclipse.core.commands.ExecutionEvent;
import org.eclipse.core.commands.ExecutionException;
import org.eclipse.jface.text.BadLocationException;
import org.eclipse.jface.text.IBlockTextSelection;
import org.eclipse.jface.text.IDocument;
import org.eclipse.jface.text.IMultiTextSelection;
import org.eclipse.jface.text.ITextSelection;
import org.eclipse.ui.handlers.HandlerUtil;
import org.eclipse.ui.texteditor.ITextEditor;
import org.eclipse.ui.texteditor.ITextEditorExtension2;

/**
 * Encodes the selected text as an application/x-www-form-urlencoded
 * value in the unsaved document: one undoable edit, no save.
 */
public final class EncodeFormValueHandler extends AbstractHandler {
    @Override
    public Object execute(ExecutionEvent event)
            throws ExecutionException {
        if (!(HandlerUtil.getActiveEditor(event)
                instanceof ITextEditor editor)) {
            return null;
        }
        if (editor instanceof ITextEditorExtension2 extended) {
            if (!extended.validateEditorInputState()) {
                return null; // read-only file or user declined
            }
        } else if (!editor.isEditable()) {
            return null;
        }
        if (!(editor.getSelectionProvider().getSelection()
                instanceof ITextSelection selection)
                || selection.getLength() <= 0) {
            return null; // caret only: isEmpty() would not catch this
        }
        if (selection instanceof IBlockTextSelection
                || selection instanceof IMultiTextSelection multi
                        && multi.getRegions().length != 1) {
            throw new ExecutionException(
                    "Select one continuous range, not a block or"
                            + " several ranges.");
        }
        IDocument document = editor.getDocumentProvider()
                .getDocument(editor.getEditorInput());
        try {
            String encoded = URLEncoder.encode(
                    document.get(selection.getOffset(),
                            selection.getLength()),
                    StandardCharsets.UTF_8);
            document.replace(selection.getOffset(),
                    selection.getLength(), encoded);
            editor.selectAndReveal(selection.getOffset(),
                    encoded.length());
        } catch (BadLocationException e) {
            throw new ExecutionException(
                    "The selected text could not be encoded.", e);
        }
        return null;
    }
}
