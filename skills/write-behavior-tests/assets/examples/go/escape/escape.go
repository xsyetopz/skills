// Package escape quotes text with backslash escapes for '\\' and '"'.
package escape

import (
	"errors"
	"strings"
)

// Quote escapes backslashes and double quotes. It works on bytes, so
// invalid UTF-8 passes through unchanged (the fuzzer found that ranging
// over runes turned byte 0xa5 into U+FFFD).
func Quote(s string) string {
	var b strings.Builder
	for i := 0; i < len(s); i++ {
		if s[i] == '\\' || s[i] == '"' {
			b.WriteByte('\\')
		}
		b.WriteByte(s[i])
	}
	return b.String()
}

// ErrTrailingEscape reports a backslash with nothing after it.
var ErrTrailingEscape = errors.New("trailing backslash")

// Unquote reverses Quote. It never panics; bad input returns an error.
func Unquote(s string) (string, error) {
	var b strings.Builder
	for i := 0; i < len(s); i++ {
		if s[i] != '\\' {
			b.WriteByte(s[i])
			continue
		}
		if !trailingOK && i+1 == len(s) {
			return "", ErrTrailingEscape
		}
		i++
		b.WriteByte(s[i])
	}
	return b.String(), nil
}
