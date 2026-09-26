import re

import sublime_plugin


def slug(text, prefix="#"):
    text = text.strip().removeprefix(prefix).strip()
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


class SlugifySelectionCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        for region in reversed(list(self.view.sel())):
            if not region.empty():
                self.view.replace(edit, region, slug(self.view.substr(region)))
