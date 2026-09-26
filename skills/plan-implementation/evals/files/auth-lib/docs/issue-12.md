# Issue 12: clearer token function names

`mk_tok` and `check_tok` are the only public API of `auth.tokens`, and new
contributors keep asking what they do. Rename them to `create_token` and
`verify_token`. Two downstream services import the old names and upgrade
on their own schedule, so the old names must keep working for one minor
release and emit a `DeprecationWarning` when called.
