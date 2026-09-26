package org.acme.wordstats

import com.intellij.openapi.components.BaseState
import com.intellij.openapi.components.Service
import com.intellij.openapi.components.SimplePersistentStateComponent
import com.intellij.openapi.components.State
import com.intellij.openapi.components.Storage
import com.intellij.openapi.components.StoragePathMacros

/** Project-level state in the workspace file (not shared via VCS). */
@Service(Service.Level.PROJECT)
@State(
    name = "WordStatsProject",
    storages = [Storage(StoragePathMacros.WORKSPACE_FILE)],
)
class ProjectWordStats :
    SimplePersistentStateComponent<ProjectWordStats.State>(State()) {

    class State : BaseState() {
        var lastFileUrl by string()
        var lastCount by property(0)
    }

    fun record(fileUrl: String, count: Int) {
        state.lastFileUrl = fileUrl
        state.lastCount = count
    }
}
