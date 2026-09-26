package org.acme.wordstats;

import com.intellij.openapi.application.ReadAction;
import com.intellij.openapi.progress.ProgressIndicator;
import com.intellij.openapi.progress.Task;
import com.intellij.openapi.project.Project;
import com.intellij.openapi.vfs.VirtualFile;
import com.intellij.psi.PsiFile;
import com.intellij.psi.PsiManager;
import java.util.function.IntConsumer;
import org.jetbrains.annotations.NotNull;

/**
 * Progress API (obsolete for 2024.1+ Kotlin code; still the Java path):
 * runs on a background thread with a cancellable status-bar progress.
 */
public final class CountFileTask extends Task.Backgroundable {
  private final VirtualFile file;
  private final IntConsumer onSuccess;
  private int count;

  public CountFileTask(
      Project project, VirtualFile file, IntConsumer onSuccess) {
    super(project, "Counting words", true);
    this.file = file;
    this.onSuccess = onSuccess;
  }

  @Override
  public void run(@NotNull ProgressIndicator indicator) {
    Project project = getProject();
    // Background thread: cancellable read, restarted after each write.
    // ReadAction.compute is deprecated since 2026.1 (build 261).
    count = ReadAction.nonBlocking(() -> {
      if (!file.isValid()) {
        return 0;
      }
      PsiFile psi = PsiManager.getInstance(project).findFile(file);
      return psi == null ? 0 : PsiWordsKt.countPsiWords(psi);
    }).wrapProgress(indicator).executeSynchronously();
  }

  @Override
  public void onSuccess() {
    onSuccess.accept(count); // called on the EDT
  }
}
