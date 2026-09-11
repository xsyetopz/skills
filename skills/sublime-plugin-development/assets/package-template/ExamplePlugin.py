"""Encode each non-empty selection as a JSON string literal in one undo step."""

import json

import sublime_plugin


class ExampleJsonStringCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        for region in reversed(list(self.view.sel())):
            if not region.empty():
                encoded = json.dumps(self.view.substr(region), ensure_ascii=False)
                self.view.replace(edit, region, encoded)

    def is_enabled(self):
        return not self.view.is_read_only() and any(
            not region.empty() for region in self.view.sel()
        )
