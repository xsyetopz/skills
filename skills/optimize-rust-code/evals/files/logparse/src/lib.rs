//! Summarizes comma-separated service logs: `timestamp,service,level,message...`.

use std::collections::BTreeMap;

#[derive(Debug, Default, PartialEq, Eq)]
pub struct Summary {
    pub rows: usize,
    pub max_fields: usize,
    pub errors_by_service: BTreeMap<String, usize>,
}

fn parse(text: &str) -> Vec<Vec<String>> {
    let mut out = Vec::new();
    for line in text.lines() {
        let fields: Vec<String> = line.split(',').map(|f| f.to_string()).collect();
        out.push(fields);
    }
    out
}

/// The only public entry point; the CLI and the web dashboard both call it.
pub fn summarize(text: &str) -> Summary {
    let rows = parse(text);
    let mut summary = Summary::default();
    for row in &rows {
        summary.rows += 1;
        summary.max_fields = summary.max_fields.max(row.len());
        if row.len() > 2 && row[2] == "ERROR" {
            *summary.errors_by_service.entry(row[1].clone()).or_insert(0) += 1;
        }
    }
    summary
}
