package com.acme.scan;

import org.eclipse.core.resources.IFile;
import org.eclipse.core.resources.IMarker;
import org.eclipse.core.resources.IProject;
import org.eclipse.core.resources.IResource;
import org.eclipse.core.resources.IResourceProxy;
import org.eclipse.core.resources.WorkspaceJob;
import org.eclipse.core.runtime.CoreException;
import org.eclipse.core.runtime.IProgressMonitor;
import org.eclipse.core.runtime.IStatus;
import org.eclipse.core.runtime.Status;

/** Flags files larger than the limit with a com.acme.scan.large marker. */
public class ScanJob extends WorkspaceJob {
  static final String MARKER = "com.acme.scan.large";
  private static final long MAX_FILE_SIZE = 1048576;

  private final IProject project;

  public ScanJob(IProject project) {
    super("Scanning " + project.getName());
    this.project = project;
    setRule(project);
  }

  @Override
  public IStatus runInWorkspace(IProgressMonitor monitor) throws CoreException {
    project.deleteMarkers(MARKER, false, IResource.DEPTH_INFINITE);
    project.accept((IResourceProxy proxy) -> {
      if (proxy.getType() == IResource.FILE) {
        IFile file = (IFile) proxy.requestResource();
        long size = file.getLocation().toFile().length();
        if (size > MAX_FILE_SIZE) {
          IMarker m = file.createMarker(MARKER);
          m.setAttribute(IMarker.SEVERITY, IMarker.SEVERITY_WARNING);
          m.setAttribute(IMarker.MESSAGE, "File is " + size + " bytes");
        }
      }
      return true;
    }, IResource.NONE);
    return Status.OK_STATUS;
  }
}
