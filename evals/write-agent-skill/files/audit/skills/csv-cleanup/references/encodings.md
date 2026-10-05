# Encodings

## Legacy Windows exports

Try `utf-8-sig` first, then `cp1252`; record which one succeeded. Never
use `errors="ignore"`, which silently drops characters.
