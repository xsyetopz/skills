package com.acme.lint;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;

import org.eclipse.core.resources.IFile;
import org.eclipse.core.resources.IMarker;
import org.eclipse.core.resources.IResource;
import org.eclipse.core.resources.IResourceChangeEvent;
import org.eclipse.core.resources.IResourceChangeListener;
import org.eclipse.core.resources.IResourceDelta;
import org.eclipse.core.runtime.CoreException;

/** Marks lines longer than 120 characters in .txt files. */
public class LongLineListener implements IResourceChangeListener {
  static final String MARKER = "com.acme.lint.longline";

  @Override
  public void resourceChanged(IResourceChangeEvent event) {
    try {
      event.getDelta().accept((IResourceDelta delta) -> {
        if (delta.getResource() instanceof IFile file
            && "txt".equals(file.getFileExtension())
            && (delta.getFlags() & IResourceDelta.CONTENT) != 0) {
          file.deleteMarkers(MARKER, false, IResource.DEPTH_ZERO);
          try (BufferedReader in = new BufferedReader(new InputStreamReader(
              file.getContents(), StandardCharsets.UTF_8))) {
            String line;
            int n = 0;
            while ((line = in.readLine()) != null) {
              n++;
              if (line.length() > 120) {
                IMarker m = file.createMarker(MARKER);
                m.setAttribute(IMarker.LINE_NUMBER, n);
                m.setAttribute(IMarker.MESSAGE, "Line longer than 120 characters");
              }
            }
          } catch (IOException e) {
            throw new CoreException(org.eclipse.core.runtime.Status.error("read", e));
          }
        }
        return true;
      });
    } catch (CoreException e) {
      e.printStackTrace();
    }
  }
}
