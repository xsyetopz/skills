package org.acme.wordstats

import com.intellij.openapi.components.service
import com.intellij.openapi.options.BoundConfigurable
import com.intellij.openapi.ui.DialogPanel
import com.intellij.ui.dsl.builder.bindIntText
import com.intellij.ui.dsl.builder.bindSelected
import com.intellij.ui.dsl.builder.panel

/**
 * applicationConfigurable: no-argument constructor, no work in it. The
 * panel is built only when the user opens Settings | Tools | Word Stats;
 * apply(), reset(), and isModified() come from the bindings.
 */
class WordStatsConfigurable : BoundConfigurable("Word Stats") {
    override fun createPanel(): DialogPanel {
        val settings = service<WordStatsSettings>()
        return panel {
            row("Minimum word length:") {
                intTextField(1..50).bindIntText(settings::minLength)
            }
            row {
                checkBox("Notify when counting finishes")
                    .bindSelected(settings::notifyOnFinish)
            }
        }
    }
}
