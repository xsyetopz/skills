# pyright: reportAttributeAccessIssue=false
"""change_id + transform_region_from: apply a worker result after edits.

Compiled only (Python 3.8 and 3.14); not part of TodoLens. The worker
uppercases the first selection; if the user edits elsewhere meanwhile,
the region is mapped to its new position; if the selected text itself
changed, the result is discarded.
"""

import sublime
import sublime_plugin


class UpperAsyncCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        view = self.view
        region = view.sel()[0]
        if region.empty():
            return
        change_id = view.change_id()
        original = view.substr(region)

        def work():
            result = original.upper()  # stands in for slow work
            args = {
                "change_id": list(change_id),
                "a": region.begin(),
                "b": region.end(),
                "original": original,
                "text": result,
            }
            sublime.set_timeout(lambda: view.run_command("upper_async_apply", args), 0)

        sublime.set_timeout_async(work, 0)


class UpperAsyncApplyCommand(sublime_plugin.TextCommand):
    def run(self, edit, change_id, a, b, original, text):
        region = self.view.transform_region_from(sublime.Region(a, b), tuple(change_id))
        if self.view.substr(region) != original:
            return  # the selected text itself changed: stale result
        self.view.replace(edit, region, text)
