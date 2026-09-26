//! fetchd library: configuration and the fetch loop.

pub mod config;

pub use config::Config;

/// Number of fetch attempts the loop makes for one URL.
pub fn attempts(config: &Config) -> u32 {
    if config.retries_enabled { config.max_retries + 1 } else { 1 }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn attempts_include_first_try() {
        let config = Config::default();
        assert_eq!(attempts(&config), 4);
        let off = Config { retries_enabled: false, ..Config::default() };
        assert_eq!(attempts(&off), 1);
    }
}
