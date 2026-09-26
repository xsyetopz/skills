# TODO Owner

Reports `TODO` comments without an owner in plain text and Markdown
files and offers a quick fix that inserts `(owner)` after `TODO`.

## Settings

- `todoOwner.enable`: report unowned TODOs.
- `todoOwner.severity`: `error`, `warning`, `information`, or `hint`.
- `todoOwner.defaultOwner`: owner inserted by the quick fix.
- `todoOwner.trimTrailingWhitespaceOnSave`: trim TODO lines on save.
- `todoOwner.gitPath`: git executable; ignored in untrusted workspaces.
