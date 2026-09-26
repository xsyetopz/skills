import json

import sublime
import sublime_plugin


def tidy(text):
    return json.dumps(json.loads(text), indent=2, sort_keys=True) + "\n"


class JsonTidyCommand(sublime_plugin.TextCommand):
    """Reformat the whole buffer as JSON without blocking typing."""

    def run(self, edit):
        text = self.view.substr(sublime.Region(0, self.view.size()))
        sublime.set_timeout_async(lambda: self.apply(edit, tidy(text)))

    def apply(self, edit, out):
        self.view.replace(edit, sublime.Region(0, self.view.size()), out)
