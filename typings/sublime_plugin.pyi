import sublime

class TextCommand:
    view: sublime.View

    def __init__(self, view: sublime.View) -> None: ...
