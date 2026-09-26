// Must NOT compile: arguments are swapped. verify.sh expects error E0308.
mod ids {
    include!("ids.rs");
}
use ids::{membership_key, TenantId, UserId};

pub fn wrong(user: UserId, tenant: TenantId) -> String {
    membership_key(tenant, user)
}
