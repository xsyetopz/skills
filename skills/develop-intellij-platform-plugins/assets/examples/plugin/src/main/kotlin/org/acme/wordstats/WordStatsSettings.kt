package org.acme.wordstats

import com.intellij.openapi.components.RoamingType
import com.intellij.openapi.components.SerializablePersistentStateComponent
import com.intellij.openapi.components.Service
import com.intellij.openapi.components.State
import com.intellij.openapi.components.Storage

/** Application-level light service; light app PSC must disable roaming. */
@Service
@State(
    name = "WordStatsSettings",
    storages = [
        Storage("wordStats.xml", roamingType = RoamingType.DISABLED),
    ],
)
class WordStatsSettings :
    SerializablePersistentStateComponent<WordStatsSettings.State>(State()) {

    var minLength: Int
        get() = state.minLength
        set(value) {
            updateState { it.copy(minLength = value) }
        }

    var notifyOnFinish: Boolean
        get() = state.notifyOnFinish
        set(value) {
            updateState { it.copy(notifyOnFinish = value) }
        }

    data class State(
        @JvmField val minLength: Int = 1,
        @JvmField val notifyOnFinish: Boolean = true,
    )
}
