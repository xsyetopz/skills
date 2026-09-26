package org.acme.todos.tests;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertThrows;

import java.nio.file.Files;
import java.nio.file.Path;

import org.eclipse.core.commands.ExecutionException;
import org.eclipse.core.filesystem.EFS;
import org.eclipse.jface.text.BlockTextSelection;
import org.eclipse.jface.text.IDocument;
import org.eclipse.jface.text.IRegion;
import org.eclipse.jface.text.ITextSelection;
import org.eclipse.jface.text.MultiTextSelection;
import org.eclipse.jface.text.Region;
import org.eclipse.ui.IWorkbenchPage;
import org.eclipse.ui.IWorkbenchWindow;
import org.eclipse.ui.PlatformUI;
import org.eclipse.ui.handlers.IHandlerService;
import org.eclipse.ui.ide.IDE;
import org.eclipse.ui.texteditor.ITextEditor;
import org.eclipse.ui.texteditor.ITextEditorActionConstants;
import org.eclipse.ui.texteditor.ITextEditorExtension5;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;

public class EncodeFormValueIT {
    private static final String ENCODE = "org.acme.todos.encodeFormValue";

    private IWorkbenchWindow window;
    private IWorkbenchPage page;
    private Path file;
    private ITextEditor editor;
    private IDocument document;

    private void open(String text) throws Exception {
        file = Files.createTempFile("form-value-", ".txt");
        Files.writeString(file, text);
        editor = (ITextEditor) IDE.openEditorOnFileStore(page,
                EFS.getLocalFileSystem().getStore(file.toUri()));
        document = editor.getDocumentProvider()
                .getDocument(editor.getEditorInput());
    }

    private void encode() throws Exception {
        window.getService(IHandlerService.class)
                .executeCommand(ENCODE, null);
    }

    @Before
    public void setUp() {
        window = PlatformUI.getWorkbench().getActiveWorkbenchWindow();
        page = window.getActivePage();
    }

    @After
    public void tearDown() throws Exception {
        page.closeEditor(editor, false);
        Files.delete(file);
    }

    @Test
    public void encodesUnsavedSelectionAsOneUndoableEdit()
            throws Exception {
        open("prefix saved suffix");
        document.replace(7, 5, "a b+é");
        editor.selectAndReveal(7, 5);
        encode();
        assertEquals("prefix a+b%2B%C3%A9 suffix", document.get());
        ITextSelection selection = (ITextSelection)
                editor.getSelectionProvider().getSelection();
        assertEquals("a+b%2B%C3%A9", selection.getText());
        editor.getAction(ITextEditorActionConstants.UNDO).run();
        assertEquals("prefix a b+é suffix", document.get());
        assertEquals("prefix saved suffix", Files.readString(file));
    }

    @Test
    public void caretOnlySelectionLeavesEditorClean() throws Exception {
        open("unchanged");
        editor.selectAndReveal(0, 0);
        encode();
        assertFalse(editor.isDirty());
        assertEquals("unchanged", document.get());
    }

    @Test
    public void rejectsMultiAndBlockSelections() throws Exception {
        open("a b unchanged c d");
        editor.getSelectionProvider().setSelection(new MultiTextSelection(
                document, new IRegion[] {new Region(0, 3),
                    new Region(14, 3)}));
        assertThrows(ExecutionException.class, this::encode);
        ((ITextEditorExtension5) editor).setBlockSelectionMode(true);
        editor.getSelectionProvider().setSelection(
                new BlockTextSelection(document, 0, 0, 0, 3, 4));
        assertThrows(ExecutionException.class, this::encode);
        assertEquals("a b unchanged c d", document.get());
        assertFalse(editor.isDirty());
    }
}
