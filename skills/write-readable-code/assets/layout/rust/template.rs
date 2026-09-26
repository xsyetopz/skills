// One module file. In a crate, the inline module bodies below are
// `mod name;` declarations backed by files.
mod private_module {}
pub(crate) mod crate_module {}
pub mod public_module {}

use std::fmt;

pub const PUBLIC_CONSTANT: usize = 1;
pub(crate) const CRATE_CONSTANT: usize = 2;
const PRIVATE_CONSTANT: usize = 4;

pub struct PublicType {
    field: usize,
}

impl PublicType {
    pub fn new() -> Self {
        Self {
            field: PRIVATE_CONSTANT,
        }
    }

    pub fn public_method(&self) -> usize {
        self.private_method() + CRATE_CONSTANT
    }

    pub(crate) fn crate_method(&self) -> usize {
        self.field
    }

    fn private_method(&self) -> usize {
        private_helper(self.field)
    }
}

impl Default for PublicType {
    fn default() -> Self {
        Self::new()
    }
}

impl fmt::Display for PublicType {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "PublicType({})", self.crate_method())
    }
}

struct PrivateType;

fn private_helper(value: usize) -> usize {
    let _ = PrivateType;
    value * PUBLIC_CONSTANT
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn public_method_adds_crate_constant() {
        assert_eq!(PublicType::new().public_method(), 6);
    }
}
