package constructs

import "strings"

// Header is small enough to return by value.
type Header struct {
	Name  string
	Value string
	Size  int
}

// ParseHeaderBaseline returns a pointer, so the Header escapes to the heap
// whenever the call is not inlined into a caller that keeps it local.
func ParseHeaderBaseline(line string) *Header {
	name, value, ok := strings.Cut(line, ":")
	if !ok {
		return nil
	}
	name = strings.TrimSpace(name)
	value = strings.TrimSpace(value)
	if name == "" || strings.ContainsAny(name, " \t") {
		return nil
	}
	return &Header{Name: name, Value: value, Size: len(line)}
}
