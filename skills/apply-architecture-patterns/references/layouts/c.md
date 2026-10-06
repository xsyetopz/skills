# C

Visibility is linkage.
A symbol is `static` in the `.c` file unless another translation unit calls it.
Only symbols that other files call are declared in the `.h` file.
Never put a non-exported symbol in a header.

## Order in a `.c` file

1. Own header first, so the header proves it is self-contained.
1. System headers, then project headers.
1. Macros and constants.
1. Private types.
1. Forward declarations of `static` functions.
1. Public definitions, in the order the header declares them.
1. `static` helpers.

## Order in a `.h` file

1. Include guard (`#pragma once` only if the project already uses it).
1. Includes the header itself needs, and no others.
1. `extern "C"` guard, if C++ code includes the header.
1. Public constants and macros.
1. Opaque type declarations (`struct component;`) and public types.
1. Public function declarations.

Tests go in a separate `tests/` directory and call the public API.
Do not add `#ifdef TEST` blocks to production files.

## Template

```c
/* component.c */
#include "component.h"

#include <stddef.h>
#include <stdint.h>

#define LOCAL_MACRO 1

static constexpr size_t LOCAL_LIMIT = 64; /* C23; use static const before C23 */

struct component {
    int value;
};

static void private_helper(struct component *state);

void component_public_function(struct component *state)
{
    private_helper(state);
}

static void private_helper(struct component *state)
{
    state->value = LOCAL_MACRO;
}
```

```c
/* component.h */
#ifndef PROJECT_COMPONENT_H
#define PROJECT_COMPONENT_H

#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

#define COMPONENT_PUBLIC_CONSTANT 1

struct component;

void component_public_function(struct component *state);

#ifdef __cplusplus
}
#endif

#endif
```
