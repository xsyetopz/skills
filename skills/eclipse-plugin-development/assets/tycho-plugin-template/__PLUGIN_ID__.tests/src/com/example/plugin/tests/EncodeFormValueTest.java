package __JAVA_PACKAGE__.tests;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertThrows;

import org.eclipse.core.commands.ExecutionException;
import org.eclipse.core.filesystem.EFS;
import org.eclipse.jface.text.BlockTextSelection;
import org.eclipse.jface.text.IRegion;
import org.eclipse.jface.text.ITextSelection;
import org.eclipse.jface.text.MultiTextSelection;
import org.eclipse.jface.text.Region;
import org.eclipse.ui.PlatformUI;
import org.eclipse.ui.handlers.IHandlerService;
import org.eclipse.ui.ide.IDE;
import org.eclipse.ui.texteditor.ITextEditor;
import org.eclipse.ui.texteditor.ITextEditorActionConstants;
import org.eclipse.ui.texteditor.ITextEditorExtension5;
import org.junit.Test;

import java.nio.file.Files;

public class EncodeFormValueTest {
    @Test
    public void encodesSelectedUnsavedTextAndUndoesOnce() throws Exception {
        var file = Files.createTempFile("form-value-", ".txt");
        Files.writeString(file, "prefix saved suffix");
        var window = PlatformUI.getWorkbench().getActiveWorkbenchWindow();
        var page = window.getActivePage();
        var editor =
                (ITextEditor)
                        IDE.openEditorOnFileStore(
                                page, EFS.getLocalFileSystem().getStore(file.toUri()));
        try {
            var document = editor.getDocumentProvider().getDocument(editor.getEditorInput());
            document.replace(7, 5, "a b+é");
            editor.selectAndReveal(7, 5);
            window.getService(IHandlerService.class)
                    .executeCommand("__PLUGIN_ID__.commands.encodeFormValue", null);
            assertEquals("prefix a+b%2B%C3%A9 suffix", document.get());
            var selection = (ITextSelection) editor.getSelectionProvider().getSelection();
            assertEquals("a+b%2B%C3%A9", selection.getText());
            editor.getAction(ITextEditorActionConstants.UNDO).run();
            assertEquals("prefix a b+é suffix", document.get());
            assertEquals("prefix saved suffix", Files.readString(file));
        } finally {
            page.closeEditor(editor, false);
            Files.delete(file);
        }
    }

    @Test
    public void emptySelectionLeavesCleanDocumentUnchanged() throws Exception {
        var file = Files.createTempFile("form-value-empty-", ".txt");
        Files.writeString(file, "unchanged");
        var window = PlatformUI.getWorkbench().getActiveWorkbenchWindow();
        var page = window.getActivePage();
        var editor =
                (ITextEditor)
                        IDE.openEditorOnFileStore(
                                page, EFS.getLocalFileSystem().getStore(file.toUri()));
        try {
            editor.selectAndReveal(0, 0);
            window.getService(IHandlerService.class)
                    .executeCommand("__PLUGIN_ID__.commands.encodeFormValue", null);
            assertFalse(editor.isDirty());
            assertEquals(
                    0, ((ITextSelection) editor.getSelectionProvider().getSelection()).getLength());
            assertEquals(
                    "unchanged",
                    editor.getDocumentProvider().getDocument(editor.getEditorInput()).get());
        } finally {
            page.closeEditor(editor, false);
            Files.delete(file);
        }
    }

    @Test
    public void rejectsDisjointRangesWithoutEditingBetweenThem() throws Exception {
        var file = Files.createTempFile("form-value-multi-", ".txt");
        Files.writeString(file, "a b unchanged c d");
        var window = PlatformUI.getWorkbench().getActiveWorkbenchWindow();
        var page = window.getActivePage();
        var editor =
                (ITextEditor)
                        IDE.openEditorOnFileStore(
                                page, EFS.getLocalFileSystem().getStore(file.toUri()));
        try {
            var document = editor.getDocumentProvider().getDocument(editor.getEditorInput());
            editor.getSelectionProvider()
                    .setSelection(
                            new MultiTextSelection(
                                    document, new IRegion[] {new Region(0, 3), new Region(14, 3)}));
            assertThrows(
                    ExecutionException.class,
                    () ->
                            window.getService(IHandlerService.class)
                                    .executeCommand(
                                            "__PLUGIN_ID__.commands.encodeFormValue", null));
            assertEquals("a b unchanged c d", document.get());
            assertFalse(editor.isDirty());
            ((ITextEditorExtension5) editor).setBlockSelectionMode(true);
            editor.getSelectionProvider()
                    .setSelection(new BlockTextSelection(document, 0, 0, 0, 3, 4));
            assertThrows(
                    ExecutionException.class,
                    () ->
                            window.getService(IHandlerService.class)
                                    .executeCommand(
                                            "__PLUGIN_ID__.commands.encodeFormValue", null));
            assertEquals("a b unchanged c d", document.get());
            assertFalse(editor.isDirty());
        } finally {
            page.closeEditor(editor, false);
            Files.delete(file);
        }
    }
}
