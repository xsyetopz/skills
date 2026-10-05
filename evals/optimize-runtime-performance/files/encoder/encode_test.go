package encoder

import "testing"

func TestEncode(t *testing.T) {
	got := Encode([]Field{{"status", 200}, {"bytes", -1}})
	if want := "status=200 bytes=-1 "; got != want {
		t.Fatalf("Encode = %q, want %q", got, want)
	}
}

var sink string

func BenchmarkEncode(b *testing.B) {
	fields := make([]Field, 20)
	for i := range fields {
		fields[i] = Field{Key: "field", Val: int64(100000 + i*7919)}
	}
	b.ReportAllocs()
	for i := 0; i < b.N; i++ {
		sink = Encode(fields)
	}
}
