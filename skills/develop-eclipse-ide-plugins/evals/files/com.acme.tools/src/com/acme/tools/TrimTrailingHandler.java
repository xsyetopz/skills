package com.acme.tools;

import org.eclipse.core.commands.AbstractHandler;
import org.eclipse.core.commands.ExecutionEvent;
import org.eclipse.jface.text.IDocument;
import org.eclipse.ui.handlers.HandlerUtil;
import org.eclipse.ui.texteditor.ITextEditor;

public class TrimTrailingHandler extends AbstractHandler {
  @Override
  public Object execute(ExecutionEvent event) {
    if (HandlerUtil.getActiveEditor(event) instanceof ITextEditor editor) {
      IDocument doc = editor.getDocumentProvider()
          .getDocument(editor.getEditorInput());
      doc.set(doc.get().replaceAll("[ \\t]+(\\r?\\n)", "$1"));
    }
    return null;
  }
}
