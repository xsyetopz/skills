# Go

Capitalization is the API boundary: there are no visibility keywords.
An identifier is unexported unless another package must use it.
To hide a whole package from outside a module subtree, put it under `internal/`.
Avoid exported mutable package variables; export a function or a sentinel error instead.

## Order in a file

1. `package` clause, with the package comment in one file only.
1. `import` block: standard library, blank line, then everything else (`goimports` groups).
1. Constants.
1. Variables, including sentinel errors.
1. Each type, then its constructor, then its methods.
1. Unexported types and helper functions, after the code that uses them.

Keep methods in the same file as their receiver type.
Tests go beside the code in `<name>_test.go`.
Use `package component_test` to test the exported API,
and `package component` only for a test that needs unexported names.

## Template

The file below is indented with spaces only so that Markdown lint passes; `gofmt` uses tabs.

```go
package component

import (
    "errors"
    "fmt"
)

const (
    PublicConstant  = 1
    privateConstant = 2
)

var ErrInvalid = errors.New("component: invalid")

type PublicType struct {
    PublicField  int
    privateField int
}

func NewPublicType() *PublicType {
    return &PublicType{privateField: privateConstant}
}

func (p *PublicType) PublicMethod() error {
    return p.privateMethod()
}

func (p *PublicType) privateMethod() error {
    if p.privateField < 0 {
        return fmt.Errorf("private field %d: %w", p.privateField, ErrInvalid)
    }
    return nil
}

type privateType struct {
    value int
}

func privateHelper(t privateType) int {
    return t.value
}
```
