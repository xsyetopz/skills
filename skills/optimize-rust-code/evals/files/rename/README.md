# fetchd

Create a `Config` with `Config::default()` and pass it to `attempts`:

```rust
let config = fetchd::Config::default();
assert_eq!(fetchd::attempts(&config), 4);
```
