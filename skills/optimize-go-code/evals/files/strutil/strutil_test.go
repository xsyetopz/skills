package strutil

import "testing"

func TestHelpers(t *testing.T) {
	if got := Trim_Spaces("  a b "); got != "a b" {
		t.Errorf("Trim_Spaces = %q", got)
	}
	if got := Get_Initials("ada king lovelace"); got != "AKL" {
		t.Errorf("Get_Initials = %q", got)
	}
	if got := Join_With_Comma([]string{"x", "y"}); got != "x, y" {
		t.Errorf("Join_With_Comma = %q", got)
	}
}
