package org.acme.wordstats;

import com.intellij.openapi.components.PersistentStateComponent;
import com.intellij.openapi.components.RoamingType;
import com.intellij.openapi.components.Service;
import com.intellij.openapi.components.State;
import com.intellij.openapi.components.Storage;
import java.util.ArrayList;
import java.util.List;
import org.jetbrains.annotations.NotNull;

/** Java PersistentStateComponent with a separate state class. */
@Service
@State(
    name = "WordStatsRunLog",
    storages = @Storage(
        value = "wordStatsRunLog.xml",
        roamingType = RoamingType.DISABLED))
public final class LegacyRunLog
    implements PersistentStateComponent<LegacyRunLog.RunState> {

  /** Serialized by public fields; needs a no-argument constructor. */
  public static final class RunState {
    public int runs;
    public List<String> recentFiles = new ArrayList<>();
  }

  private RunState state = new RunState();

  @Override
  public @NotNull RunState getState() {
    return state;
  }

  @Override
  public void loadState(@NotNull RunState loaded) {
    state = loaded;
  }

  public synchronized void recordRun(String fileName) {
    state.runs++;
    state.recentFiles.add(0, fileName);
    if (state.recentFiles.size() > 5) {
      state.recentFiles.remove(5);
    }
  }
}
