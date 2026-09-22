# Extension case studies for Sublime Python Plugin

## Sublime Text: asynchronous analysis without retaining Edit

```python
class AnalyzeCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        view_id = self.view.id()
        change_count = self.view.change_count()
        text = self.view.substr(sublime.Region(0, self.view.size()))
        sublime.set_timeout_async(
            lambda: self._analyze(view_id, change_count, text), 0)

    def _analyze(self, view_id, change_count, text):
        result = analyze(text)
        callback = lambda: publish_if_fresh(
            view_id, change_count, result
        )
        sublime.set_timeout(callback, 0)
```

`publish_if_fresh` resolves the view, checks it still exists and has the same
change count, then invokes a new TextCommand for edits. Host tests remain
required.

## Lifecycle evidence checklist

- activate/load once and twice;
- invoke normal and failing inputs;
- start async work, then edit/close/dispose before completion;
- cancel and verify no late publication;
- unload/reload or close/reopen project/workspace;
- inspect duplicate registrations, processes, timers, handles, and persisted
  state;
- build package, inspect contents, install in a clean declared host;
- distinguish stub/unit tests from real host execution.
