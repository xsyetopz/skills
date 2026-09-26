# pyright: reportAttributeAccessIssue=false
"""load_resource: read a file shipped in a package, packed or loose.

Compiled only (Python 3.8 and 3.14). Resource names use the
"Packages/<Package>/<path>" form even when the package is a zipped
.sublime-package, where no file exists on disk to open().
"""

import sublime
import sublime_plugin

RESOURCE = "Packages/TodoLens/TodoLens.sublime-settings"


class TodoLensShowDefaultsCommand(sublime_plugin.WindowCommand):
    def run(self):
        try:
            text = sublime.load_resource(RESOURCE)
        except FileNotFoundError:
            matches = sublime.find_resources("TodoLens.sublime-settings")
            sublime.error_message("TodoLens: not found; candidates: %s" % matches)
            return
        view = self.window.new_file()
        view.set_scratch(True)
        view.set_name("TodoLens defaults")
        view.run_command("append", {"characters": text})
        view.set_read_only(True)
