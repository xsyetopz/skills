use pairs::*;

#[test]
fn differential_small_domain() {
    for length in 0..=5_u32 {
        for mut code in 0..3_usize.pow(length) {
            let mut values = Vec::new();
            for _ in 0..length { values.push((code % 3) as i64 - 1); code /= 3; }
            let saved = values.clone();
            let strings: Vec<String> = values.iter().map(ToString::to_string).collect();
            assert_eq!(baseline_append(&values), candidate_append(&values));
            assert_eq!(baseline_counts(&strings), candidate_counts(&strings));
            assert_eq!(baseline_membership(&strings, &strings), candidate_membership(&strings, &strings));
            assert_eq!(baseline_sum(&values), candidate_sum(&values));
            assert_eq!(baseline_queue(&values), candidate_queue(&values));
            let text = strings.join(":");
            assert_eq!(baseline_delimiters(&text), candidate_delimiters(&text));
            assert_eq!(baseline_owned_lengths(&strings), candidate_cow_clone_from_lengths(&strings));
            assert_eq!(baseline_aos_x_sum(&values), candidate_soa_x_sum(&values));
            assert_eq!(values, saved);
        }
    }
}
#[test]
fn independent_expected_results_and_unicode() {
    let values = ["é", "e\u{301}", "é", "🙂", "\0"].map(String::from);
    let expected = vec![("é".into(), 2), ("e\u{301}".into(), 1), ("🙂".into(), 1), ("\0".into(), 1)];
    assert_eq!(baseline_counts(&values), expected);
    assert_eq!(candidate_counts(&values), expected);
    let queries = ["é", "missing"].map(String::from);
    assert_eq!(baseline_membership(&values, &queries), vec![true, false]);
    assert_eq!(candidate_membership(&values, &queries), vec![true, false]);
    assert_eq!(baseline_sum(&[-3, 2, 2, 0, 5]), 8);
    assert_eq!(candidate_sum(&[-3, 2, 2, 0, 5]), 8);
    for text in ["", "a", "é", "🙂", "："] {
        assert_eq!(baseline_delimiters(text), 0); assert_eq!(candidate_delimiters(text), 0);
    }
    assert_eq!(baseline_delimiters(":é::🙂:"), 4);
    assert_eq!(candidate_delimiters(":é::🙂:"), 4);
    assert_eq!(candidate_append(&[i64::MIN, i64::MAX]), vec![i64::MIN, i64::MAX]);
    assert_eq!(baseline_queue(&[2, 1, 2]), vec![2, 1, 2]);
    assert_eq!(candidate_queue(&[2, 1, 2]), vec![2, 1, 2]);
}
#[test]
fn rejected_flag_and_capacity_substitutions() {
    let mask = 0b0011_u8;
    let value = 0b0001_u8;
    assert!((value & mask) != 0); // any bit, NOT all bits
    assert_ne!(value & mask, mask);
    let capacity_only: Vec<u64> = Vec::with_capacity(8);
    assert_eq!(capacity_only.len(), 0); // reserve is not initialization
    assert!(capacity_only.get(0).is_none());
}
