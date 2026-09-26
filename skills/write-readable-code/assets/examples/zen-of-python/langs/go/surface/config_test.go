package surface

import "testing"

func TestParse(t *testing.T) {
	c, err := Parse("Port = 80\n\nhost=a")
	if err != nil {
		t.Fatal(err)
	}
	if v, ok := c.Get("PORT"); !ok || v != "80" {
		t.Fatalf("port = %q, %v", v, ok)
	}
	if _, err := Parse("novalue"); err == nil {
		t.Fatal("expected error for a line without '='")
	}
}
