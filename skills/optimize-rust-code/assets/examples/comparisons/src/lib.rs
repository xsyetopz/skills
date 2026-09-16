#![forbid(unsafe_code)]
use std::collections::{HashMap, HashSet, VecDeque};
use std::borrow::Cow;

pub fn baseline_append(values: &[i64]) -> Vec<i64> {
    let mut result = Vec::new();
    for &value in values {
        result = [result.as_slice(), &[value]].concat();
    }
    result
}
pub fn candidate_append(values: &[i64]) -> Vec<i64> {
    let mut result = Vec::with_capacity(values.len());
    for &value in values { result.push(value); }
    result
}
pub fn baseline_counts(values: &[String]) -> Vec<(String, usize)> {
    let mut counts: Vec<(String, usize)> = Vec::new();
    for value in values {
        if let Some(pair) = counts.iter_mut().find(|pair| pair.0 == *value) {
            pair.1 += 1;
        } else {
            counts.push((value.clone(), 1));
        }
    }
    counts
}
pub fn candidate_counts(values: &[String]) -> Vec<(String, usize)> {
    let mut indices: HashMap<&str, usize> = HashMap::new();
    let mut counts: Vec<(String, usize)> = Vec::new();
    for value in values {
        let next = counts.len();
        let index = *indices.entry(value.as_str()).or_insert(next);
        if index == next { counts.push((value.clone(), 1)); }
        else { counts[index].1 += 1; }
    }
    counts
}
pub fn baseline_membership(values: &[String], queries: &[String]) -> Vec<bool> {
    queries.iter().map(|query| values.contains(query)).collect()
}
pub fn candidate_membership(values: &[String], queries: &[String]) -> Vec<bool> {
    let members: HashSet<&str> = values.iter().map(String::as_str).collect();
    queries.iter().map(|query| members.contains(query.as_str())).collect()
}
pub fn baseline_sum(values: &[i64]) -> i64 {
    let selected: Vec<i64> = values.iter().copied().filter(|value| value % 2 == 0).collect();
    let squared: Vec<i64> = selected.iter().map(|value| value * value).collect();
    squared.iter().sum()
}
pub fn candidate_sum(values: &[i64]) -> i64 {
    values.iter().filter(|value| *value % 2 == 0).map(|value| value * value).sum()
}
pub fn baseline_queue(values: &[i64]) -> Vec<i64> {
    let mut pending = values.to_vec();
    let mut result = Vec::new();
    while !pending.is_empty() { result.push(pending.remove(0)); }
    result
}
pub fn candidate_queue(values: &[i64]) -> Vec<i64> {
    let mut pending: VecDeque<i64> = values.iter().copied().collect();
    let mut result = Vec::new();
    while let Some(value) = pending.pop_front() { result.push(value); }
    result
}
pub fn baseline_delimiters(text: &str) -> usize {
    text.split(':').collect::<Vec<_>>().len() - 1
}
pub fn candidate_delimiters(text: &str) -> usize {
    text.bytes().filter(|&byte| byte == b':').count()
}
pub fn baseline_owned_lengths(values: &[String]) -> usize {
    let owned: Vec<String> = values.iter().map(|value| value.to_owned()).collect();
    owned.iter().map(String::len).sum()
}
pub fn candidate_cow_clone_from_lengths(values: &[String]) -> usize {
    let mut scratch = String::new();
    let mut total = 0;
    for value in values {
        let value: Cow<'_, str> = Cow::Borrowed(value.as_str());
        scratch.clone_from(&value.into_owned());
        total += scratch.len();
    }
    total
}
#[derive(Clone, Copy)]
struct Record { x: f64, y: f64 }
struct Records { x: Vec<f64>, y: Vec<f64> }
pub fn baseline_aos_x_sum(values: &[i64]) -> f64 {
    let records: Vec<Record> = values.iter().enumerate()
        .map(|(index, &value)| Record { x: value as f64, y: index as f64 })
        .collect();
    std::hint::black_box(records.iter().map(|record| record.y).sum::<f64>());
    records.iter().map(|record| record.x).sum()
}
pub fn candidate_soa_x_sum(values: &[i64]) -> f64 {
    let records = Records {
        x: values.iter().map(|&value| value as f64).collect(),
        y: (0..values.len()).map(|index| index as f64).collect(),
    };
    std::hint::black_box(records.y.iter().sum::<f64>());
    records.x.iter().sum()
}
