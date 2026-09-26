# With `set lazy` (1.47+), unused assignments are not evaluated.

set lazy

marker := `touch lazy.marker && echo created`

unrelated:
    @echo unrelated
