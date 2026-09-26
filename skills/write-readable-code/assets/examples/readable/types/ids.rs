// Distinct identifier and unit types. `cargo`-free: check with
// `rustc --edition 2024 --crate-type lib ids.rs`.

/// A user's identifier. Not interchangeable with `TenantId`.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub struct UserId(pub u64);

/// A tenant's identifier. Not interchangeable with `UserId`.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub struct TenantId(pub u64);

/// A duration in milliseconds; the unit is part of the type.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord)]
pub struct Millis(pub u64);

pub fn membership_key(user: UserId, tenant: TenantId) -> String {
    format!("{}:{}", tenant.0, user.0)
}

pub fn deadline(start: Millis, timeout: Millis) -> Millis {
    Millis(start.0 + timeout.0)
}
