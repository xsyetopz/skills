# Worked justfile examples

## Preserve failure and arguments

```just
set shell := ["bash", "-eu", "-o", "pipefail", "-c"]

test package="":
    ./scripts/test-package.sh {{quote(package)}}
```

Confirm `quote()` exists in the installed version and behaves as intended. For
complex free-text arguments, prefer a script recipe/interpreter arguments over
shell interpolation.

## Call canonical operations

```just
build:
    ./scripts/build.sh

validate: build
    ./scripts/validate.sh
```

Do not paste the implementation of both scripts into the justfile. If validate
does not always require build, remove the dependency and let callers choose.

## Failure propagation test

Use a temporary fixture whose underlying command exits 23. The recipe must exit
nonzero and preserve useful stderr; a later `echo done` must not turn it green.
