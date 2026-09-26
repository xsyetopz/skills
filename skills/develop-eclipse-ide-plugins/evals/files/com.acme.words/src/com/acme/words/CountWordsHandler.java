package com.acme.words;

import java.nio.charset.StandardCharsets;

import org.eclipse.core.commands.AbstractHandler;
import org.eclipse.core.commands.ExecutionEvent;
import org.eclipse.core.commands.ExecutionException;
import org.eclipse.core.resources.IFile;
import org.eclipse.core.resources.IMarker;
import org.eclipse.core.resources.IProject;
import org.eclipse.core.resources.IResource;
import org.eclipse.core.runtime.CoreException;
import org.eclipse.jface.dialogs.MessageDialog;
import org.eclipse.ui.handlers.HandlerUtil;

public class CountWordsHandler extends AbstractHandler {
  @Override
  public Object execute(ExecutionEvent event) throws ExecutionException {
    IProject project = (IProject) HandlerUtil.getCurrentStructuredSelection(event)
        .getFirstElement();
    int words = 0;
    try {
      for (IResource r : project.members()) {
        if (r instanceof IFile f && "txt".equals(f.getFileExtension())) {
          String text = new String(f.getContents().readAllBytes(),
              StandardCharsets.UTF_8);
          words += text.isBlank() ? 0 : text.trim().split("\\s+").length;
        }
      }
      IMarker marker = project.createMarker(IMarker.TASK);
      marker.setAttribute(IMarker.MESSAGE, words + " words");
    } catch (CoreException | java.io.IOException e) {
      throw new ExecutionException("Count failed", e);
    }
    MessageDialog.openInformation(HandlerUtil.getActiveShell(event), "Words",
        project.getName() + ": " + words + " words");
    return null;
  }
}
