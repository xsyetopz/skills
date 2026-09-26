import re

import sublime
import sublime_plugin

NOTE = re.compile(r"(?:#|//)\s*NOTE:\s*(.+)$")
KEY = "note_lens.notes"


def note_html(note):
    return '<body id="note-lens"><div class="note">' + note + "</div></body>"


class NoteLensListener(sublime_plugin.ViewEventListener):
    def on_load_async(self):
        self.refresh()

    def on_post_save_async(self):
        self.refresh()

    def refresh(self):
        regions, notes = [], []
        for line in self.view.lines(sublime.Region(0, self.view.size())):
            m = NOTE.search(self.view.substr(line))
            if m:
                regions.append(line)
                notes.append(note_html(m.group(1)))
        self.view.add_regions(
            KEY, regions, scope="comment", annotations=notes, annotation_color="#8fa"
        )
