# pyright: reportAttributeAccessIssue=false
"""EventListener: one instance sees every view in every window.

Compiled only (Python 3.8 and 3.14); not part of TodoLens. Behavior needs
Sublime Text: save any file and read the status bar.
"""

import time

import sublime_plugin


class SaveStampListener(sublime_plugin.EventListener):
    def on_post_save_async(self, view):
        # Worker thread: no Edit, and the view may already be closed.
        if not view.is_valid() or view.file_name() is None:
            return
        view.set_status("save_stamp", "saved " + time.strftime("%H:%M:%S"))

    def on_pre_close(self, view):
        view.erase_status("save_stamp")
