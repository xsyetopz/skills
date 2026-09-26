package com.acme.lint;

import org.eclipse.core.resources.IResourceChangeEvent;
import org.eclipse.core.resources.ResourcesPlugin;
import org.osgi.framework.BundleActivator;
import org.osgi.framework.BundleContext;

public class Activator implements BundleActivator {
  private final LongLineListener listener = new LongLineListener();

  @Override
  public void start(BundleContext context) {
    ResourcesPlugin.getWorkspace().addResourceChangeListener(listener,
        IResourceChangeEvent.POST_CHANGE);
  }

  @Override
  public void stop(BundleContext context) {
    ResourcesPlugin.getWorkspace().removeResourceChangeListener(listener);
  }
}
