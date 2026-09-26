//! Word statistics for documents uploaded to our public web service.
//! `text` is whatever the uploader sent (up to 50 MB per request).

use std::collections::HashMap;

/// Counts whitespace-separated words. Part of the crate's public API.
pub fn count_words(text: &str) -> HashMap<String, usize> {
    let mut map: HashMap<String, usize> = HashMap::new();
    for w in text.split_whitespace() {
        if map.contains_key(w) {
            *map.get_mut(w).unwrap() += 1;
        } else {
            map.insert(w.to_string(), 1);
        }
    }
    map
}
