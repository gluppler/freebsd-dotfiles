# Rust: errors and closures

`checked_add` returns `None` on overflow. Converting that to a `Result` gives the
caller an error it can propagate with `?`.

```rust
fn increment(value: u32) -> Result<u32, &'static str> {
    value.checked_add(1).ok_or("counter overflow")
}

fn visit(values: &[u32], mut callback: impl FnMut(u32)) {
    for &value in values {
        callback(value);
    }
}

fn main() -> Result<(), &'static str> {
    let next = increment(41)?;
    let mut total = 0;
    visit(&[next, 8], |value| total += value);
    assert_eq!(total, 50);
    Ok(())
}
```

`FnMut` permits the closure to update captured state. The callback runs before
`visit` returns; this example does not store it or move it to another thread.

**DOCS → RUST API** opens the installed standard-library reference, including
method signatures and formatted examples. Its search box works locally.
**RUST BOOK** explains ownership, traits, errors and concurrency. `man rustc`
and `man cargo` cover the tools.

For firmware, `nostromo-rust init` also installs `rust-docs` for its selected
toolchain. `nostromo-docs rust embedded-book` opens the local embedded book.
Board startup, interrupt attributes and HAL types depend on the chosen device;
do not copy an interrupt handler from a different architecture.
