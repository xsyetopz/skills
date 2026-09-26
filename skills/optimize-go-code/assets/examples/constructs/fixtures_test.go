package constructs

import (
	"fmt"
	"strconv"
	"strings"
)

// Shared inputs. Values stay outside 0..255 and 0..99 where the runtime
// returns static data without allocating, so baselines really allocate.

func ints(n int) []int {
	out := make([]int, n)
	for i := range out {
		out[i] = (i*7919)%100003 - 50000
	}
	return out
}

func words(n int) []string {
	out := make([]string, n)
	for i := range out {
		out[i] = "word-" + strconv.Itoa(1000+i%(n/2+1))
	}
	return out
}

// longKeys returns keys longer than 32 bytes so a string(b) conversion
// cannot use the compiler's small stack buffer.
func longKeys(n int) ([][]byte, map[string]int) {
	bs := make([][]byte, n)
	m := make(map[string]int, n)
	for i := range bs {
		k := fmt.Sprintf("tenant-%04d/resource/%08d/attribute", i, i*31)
		bs[i] = []byte(k)
		m[k] = i
	}
	return bs, m
}

func rects(n int) []Rect {
	out := make([]Rect, n)
	for i := range out {
		out[i] = Rect{W: float64(i%17) + 0.5, H: float64(i%5) + 1.25}
	}
	return out
}

func lines(values []int) string {
	var b strings.Builder
	for _, v := range values {
		b.WriteString(strconv.Itoa(v))
		b.WriteByte('\n')
	}
	return b.String()
}

func abs(values []int) []int {
	out := make([]int, len(values))
	for i, v := range values {
		out[i] = max(v, -v)
	}
	return out
}
