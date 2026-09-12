# Cursor hooks

Reviewed 2026-09-12 against the official [Cursor hooks
documentation](https://cursor.com/docs/hooks).

Project and user files are `.cursor/hooks.json` and `~/.cursor/hooks.json`.
They use schema version `1`, lower-camel-case event names, and event arrays of
command or prompt hook definitions. Project commands run from the project root;
user commands run from `~/.cursor/`. Use `.cursor/hooks/...` for project-local
scripts. Enterprise, team, project, and user sources have distinct precedence.

Commands exchange JSON over stdio. Exact input fields and whether output can
allow, deny, modify, or follow up depend on the event. Review the current event
table before copying a matcher or decision. Project hooks run only in trusted
workspaces, but trust does not make an opaque script safe.

Copy the asset to `.cursor/hooks.json` and the handler to
`.cursor/hooks/observe.py`, open a trusted disposable workspace, trigger a new
session, then remove the added entry and script to roll back.
