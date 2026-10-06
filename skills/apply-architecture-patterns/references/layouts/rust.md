# Rust

Items are private to their module by default.
Widen in steps:
`pub(super)`, `pub(crate)`, then `pub`.
Use `pub` only for what downstream crates need,
and mark a public enum or struct that may grow with `#[non_exhaustive]`.
These rules apply to the 2024 edition.

## Order in a file

1. Module declarations: `mod` private first, then `pub(super)`, `pub(crate)`, `pub`.
1. `use` declarations: `std`, external crates, then `crate::`, `super::`, and `self::`.
1. Constants and statics.
1. Each type, then its inherent `impl` block, then its trait `impl` blocks.
1. Private types and free functions, after the code that uses them.
1. `#[cfg(test)] mod tests { ... }` at the end of the file.

Unit tests live in that block and use `use super::*;`,
so they reach private items without widening them.
Integration tests go in the crate's `tests/` directory and use only the public API.

```rust
mod private_module;
pub(super) mod parent_module;
pub(crate) mod crate_module;
pub mod public_module;

use std::fmt;

pub const PUBLIC_CONSTANT: usize = 1;
pub(crate) const CRATE_CONSTANT: usize = 2;
const PRIVATE_CONSTANT: usize = 4;

pub struct PublicType {
    field: usize,
}

impl PublicType {
    pub fn new() -> Self {
        Self { field: PRIVATE_CONSTANT }
    }

    pub fn public_method(&self) -> usize {
        self.private_method()
    }

    pub(crate) fn crate_method(&self) -> usize {
        CRATE_CONSTANT + self.field
    }

    fn private_method(&self) -> usize {
        self.field
    }
}

impl Default for PublicType {
    fn default() -> Self {
        Self::new()
    }
}

impl fmt::Display for PublicType {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.field)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn private_method_returns_field() {
        assert_eq!(PublicType::new().private_method(), PRIVATE_CONSTANT);
    }
}
```
