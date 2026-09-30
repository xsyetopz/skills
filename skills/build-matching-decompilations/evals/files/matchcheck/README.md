# matchcheck

Matching decompilation of `GAME.EXE`. `orig/` holds the extracted reference
functions and is not committed. `build/` holds the functions extracted from
our build.

```sh
python3 verify.py orig/funcs build/funcs symbols.txt
```

Status: 3/3 functions match.
