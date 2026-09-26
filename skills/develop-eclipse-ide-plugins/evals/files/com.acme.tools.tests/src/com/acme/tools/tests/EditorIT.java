package com.acme.tools.tests;

import static org.junit.jupiter.api.Assertions.assertNotNull;

import org.eclipse.ui.PlatformUI;
import org.junit.jupiter.api.Test;

class EditorIT {
  @Test
  void workbenchIsRunning() {
    assertNotNull(PlatformUI.getWorkbench().getActiveWorkbenchWindow());
  }
}
