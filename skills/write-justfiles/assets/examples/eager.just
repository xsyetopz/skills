# Without `set lazy`, every assignment is evaluated on every invocation,
# including backticks the chosen recipe never uses.

marker := `touch eager.marker && echo created`

unrelated:
    @echo unrelated
