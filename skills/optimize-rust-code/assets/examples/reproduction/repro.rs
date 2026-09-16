fn main() {
    let calls = std::cell::Cell::new(0);
    let values = [1, 2, 3];
    let lazy = values.iter().map(|value| {
        calls.set(calls.get() + 1);
        value
    });
    drop(lazy);
    println!("actual calls={}", calls.get());
    println!("expected eager calls=3");
    assert_eq!(calls.get(), 0);
}
