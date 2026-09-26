//! Unless explicitly silenced: ignore exactly the NotFound case.
//! Refuse to guess: a duration without a unit is an error, not seconds.
use std::fs;
use std::io::{self, ErrorKind};
use std::path::Path;
use std::time::Duration;

/// Removes path; a missing file is the one error that is not reported.
fn remove_if_exists(path: &Path) -> io::Result<()> {
    match fs::remove_file(path) {
        Err(error) if error.kind() == ErrorKind::NotFound => Ok(()),
        other => other,
    }
}

/// Parses "250ms", "30s", or "5m". "30" is rejected: the unit is unknown.
fn parse_duration(text: &str) -> Result<Duration, String> {
    let split = text
        .find(|c: char| !c.is_ascii_digit())
        .ok_or_else(|| format!("missing unit in {text:?}; use ms, s, or m"))?;
    let (digits, unit) = text.split_at(split);
    let amount: u64 = digits
        .parse()
        .map_err(|error| format!("bad number in {text:?}: {error}"))?;
    match unit {
        "ms" => Ok(Duration::from_millis(amount)),
        "s" => Ok(Duration::from_secs(amount)),
        "m" => Ok(Duration::from_secs(amount * 60)),
        _ => Err(format!("unknown unit {unit:?} in {text:?}")),
    }
}

fn main() {
    let dir = std::env::temp_dir().join(format!("zen-{}", std::process::id()));
    fs::create_dir_all(&dir).unwrap();
    let file = dir.join("cache.bin");
    fs::write(&file, b"x").unwrap();
    remove_if_exists(&file).unwrap();
    remove_if_exists(&file).unwrap(); // already gone: silenced on purpose
    let other = remove_if_exists(&dir).unwrap_err(); // a directory: reported
    assert_ne!(other.kind(), ErrorKind::NotFound);
    fs::remove_dir(&dir).unwrap();
    println!(
        "silenced: NotFound only; directory error kept ({:?})",
        other.kind()
    );

    assert_eq!(parse_duration("250ms"), Ok(Duration::from_millis(250)));
    assert_eq!(parse_duration("5m"), Ok(Duration::from_secs(300)));
    for text in ["30", "30h", "s", ""] {
        assert!(parse_duration(text).is_err(), "{text:?} must be rejected");
    }
    println!("guess: {}", parse_duration("30").unwrap_err());
}
