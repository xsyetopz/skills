import sublime
import sublime_plugin

SETTINGS = "QuickLint.sublime-settings"


def reload_rules():
    s = sublime.load_settings(SETTINGS)
    print("QuickLint: reloaded, max_line_length =", s.get("max_line_length", 100))


def plugin_loaded():
    s = sublime.load_settings(SETTINGS)
    s.add_on_change("settings", reload_rules)


class QuickLintListener(sublime_plugin.EventListener):
    def on_post_save_async(self, view):
        limit = sublime.load_settings(SETTINGS).get("max_line_length", 100)
        long_lines = [
            r for r in view.lines(sublime.Region(0, view.size())) if r.size() > limit
        ]
        view.set_status("quick_lint", "{} long lines".format(len(long_lines)))
