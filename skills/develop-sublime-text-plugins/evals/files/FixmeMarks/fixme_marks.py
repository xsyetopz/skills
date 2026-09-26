import re

import sublime
import sublime_plugin

MARK = re.compile(r"\bFIXME\b")


def line_has_mark(view, point):
    return MARK.search(view.substr(view.line(point))) is not None


class FixmeMarksResolveCommand(sublime_plugin.TextCommand):
    """Replace FIXME with RESOLVED on every line that has a caret."""

    def run(self, edit):
        lines = []
        for sel in self.view.sel():
            line = self.view.line(sel.b)
            if line not in lines:
                lines.append(line)
        for line in reversed(lines):
            text = self.view.substr(line)
            self.view.replace(edit, line, MARK.sub("RESOLVED", text, count=1))
