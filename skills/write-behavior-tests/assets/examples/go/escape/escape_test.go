package escape

import (
	"errors"
	"testing"
)

func FuzzUnquote(f *testing.F) {
	for _, seed := range []string{"", "plain", `a\"b`, `\\`} {
		f.Add(seed)
	}
	f.Fuzz(func(t *testing.T, s string) {
		// Property 1: any input returns a value or an error; no panic.
		_, _ = Unquote(s)
		// Property 2: Unquote inverts Quote for every string.
		got, err := Unquote(Quote(s))
		if err != nil || got != s {
			t.Fatalf("Unquote(Quote(%q)) = %q, %v", s, got, err)
		}
	})
}

func TestTrailingBackslashIsAnError(t *testing.T) {
	if _, err := Unquote(`abc\`); !errors.Is(err, ErrTrailingEscape) {
		t.Fatalf("err = %v, want ErrTrailingEscape", err)
	}
}
