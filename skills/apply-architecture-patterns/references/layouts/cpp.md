# C++

Visibility is the header.
Declare in the header only what other files use.
Everything else stays in the `.cpp` file, in an unnamed namespace for internal linkage.
If the project builds with modules (C++20), the same rule applies to `export`:
export the public surface and keep the rest in the module implementation.

## Order in a header

1. `#pragma once` or the project's include guard.
1. Includes the header needs, and no others.
1. Namespace.
1. Public constants (`inline constexpr`).
1. Type declaration with `public`, then `protected`, then `private` sections.
1. Inside each section: types, construction, operations, then data.

## Order in a `.cpp` file

1. Own header first.
1. Other includes: project, then standard library.
1. Namespace.
1. Unnamed namespace with private constants and helpers.
1. Definitions, in the order the header declares them.

Tests go in a separate `tests/` tree and use the public header.
Do not add `friend` declarations or `#define private public` for tests.

## Template

```cpp
// component.hpp
#pragma once

#include <cstddef>

namespace project {

inline constexpr std::size_t kPublicLimit = 128;

class PublicType {
public:
    PublicType();

    void public_method();

private:
    void private_method();

    std::size_t count_ = 0;
};

}  // namespace project
```

```cpp
// component.cpp
#include "component.hpp"

#include <algorithm>

namespace project {

namespace {
constexpr std::size_t kPrivateLimit = 64;

std::size_t clamp_count(std::size_t value)
{
    return std::min(value, kPrivateLimit);
}
}  // namespace

PublicType::PublicType() = default;

void PublicType::public_method()
{
    private_method();
}

void PublicType::private_method()
{
    count_ = clamp_count(count_ + 1);
}

}  // namespace project
```
