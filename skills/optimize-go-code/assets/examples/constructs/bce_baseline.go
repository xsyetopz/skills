package constructs

// DotBaseline checks b[i] against len(b) on every iteration.
func DotBaseline(a, b []int) int {
	sum := 0
	for i := range a {
		sum += a[i] * b[i]
	}
	return sum
}
