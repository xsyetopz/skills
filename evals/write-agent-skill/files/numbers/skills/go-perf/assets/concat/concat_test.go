package concat

import (
	"strings"
	"testing"
)

var parts = func() []string {
	out := make([]string, 1000)
	for i := range out {
		out[i] = "item"
	}
	return out
}()

var sink string

func BenchmarkPlus(b *testing.B) {
	b.ReportAllocs()
	for i := 0; i < b.N; i++ {
		s := ""
		for _, p := range parts {
			s += p
		}
		sink = s
	}
}

func BenchmarkBuilder(b *testing.B) {
	b.ReportAllocs()
	for i := 0; i < b.N; i++ {
		var sb strings.Builder
		for _, p := range parts {
			sb.WriteString(p)
		}
		sink = sb.String()
	}
}

func BenchmarkBuilderGrow(b *testing.B) {
	b.ReportAllocs()
	for i := 0; i < b.N; i++ {
		var sb strings.Builder
		sb.Grow(4 * len(parts))
		for _, p := range parts {
			sb.WriteString(p)
		}
		sink = sb.String()
	}
}
