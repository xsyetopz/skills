//! [`Config`] holds the fetcher's tunables.

/// Fetcher configuration. Build one with [`Config::default`] and override fields.
#[derive(Debug, Clone, PartialEq)]
pub struct Config {
    pub max_retries: u32,
    pub retries_enabled: bool,
    pub user_agent: String,
}

impl Default for Config {
    fn default() -> Self {
        Config { max_retries: 3, retries_enabled: true, user_agent: "fetchd/0.4".into() }
    }
}
