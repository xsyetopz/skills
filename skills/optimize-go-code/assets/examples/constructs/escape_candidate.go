package constructs

import "strings"

// ParseHeaderCandidate returns the struct by value plus an ok flag; the
// caller's copy lives in its own frame.
func ParseHeaderCandidate(line string) (Header, bool) {
	name, value, ok := strings.Cut(line, ":")
	if !ok {
		return Header{}, false
	}
	name = strings.TrimSpace(name)
	value = strings.TrimSpace(value)
	if name == "" || strings.ContainsAny(name, " \t") {
		return Header{}, false
	}
	return Header{Name: name, Value: value, Size: len(line)}, true
}
