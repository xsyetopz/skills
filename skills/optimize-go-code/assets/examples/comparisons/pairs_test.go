package main

import (
	"bytes"
	"reflect"
	"strconv"
	"testing"
)

func checkPairs(t *testing.T, values []int) {
	t.Helper()
	texts := make([]string, len(values))
	for i, value := range values {
		texts[i] = strconv.Itoa(value)
	}
	checks := [][2]any{
		{baselineAppend(values), candidateAppend(values)},
		{baselineCounts(texts), candidateCounts(texts)},
		{baselineMembership(texts, []string{"0", "missing"}), candidateMembership(texts, []string{"0", "missing"})},
		{baselineJoin(texts), candidateJoin(texts)},
		{baselineFormat(values), candidateFormat(values)},
		{baselineSum(values), candidateSum(values)},
		{baselineInterfaceSum(values), candidateConcreteSum(values)},
		{baselinePerItemChannels(values), candidateBoundedBatch(values)},
	}
	for i, pair := range checks {
		if !reflect.DeepEqual(pair[0], pair[1]) {
			t.Fatalf("case %d: %#v != %#v", i+1, pair[0], pair[1])
		}
	}
}
func TestPairs(t *testing.T) {
	for length := 0; length <= 5; length++ {
		possibilities := 1
		for i := 0; i < length; i++ {
			possibilities *= 3
		}
		for code := 0; code < possibilities; code++ {
			rest := code
			values := make([]int, length)
			for i := range values {
				values[i] = rest%3 - 1
				rest /= 3
			}
			checkPairs(t, values)
		}
	}
	unicode := []string{"é", "e\u0301", "é", "🙂", "\x00"}
	expected := map[string]int{"é": 2, "e\u0301": 1, "🙂": 1, "\x00": 1}
	if !reflect.DeepEqual(baselineCounts(unicode), expected) || !reflect.DeepEqual(candidateCounts(unicode), expected) {
		t.Fatal("counts expected result")
	}
	for _, fn := range []func([]string) string{baselineJoin, candidateJoin} {
		if fn([]string{"a", "", "é", "🙂"}) != "aé🙂" {
			t.Fatal("join expected result")
		}
	}
	for _, fn := range []func([]int) []byte{baselineFormat, candidateFormat} {
		if string(fn([]int{-3, 0, 12})) != "-3,0,12" {
			t.Fatal("format expected result")
		}
	}
	for _, fn := range []func([]int) int64{baselineSum, candidateSum} {
		if fn([]int{-3, 2, 2, 0, 5}) != 8 {
			t.Fatal("sum expected result")
		}
	}
	values := []int{2, 1, 2}
	a, b := baselineAppend(values), candidateAppend(values)
	if !reflect.DeepEqual(a, values) || !reflect.DeepEqual(b, values) {
		t.Fatal("append expected result")
	}
	a[0], b[0] = 9, 8
	if values[0] != 2 {
		t.Fatal("result aliases caller storage")
	}
	owner := []byte{1, 2}
	view, copied := owner[:1], append([]byte(nil), owner[:1]...)
	owner[0] = 9
	if bytes.Equal(view, copied) {
		t.Fatal("aliasing trap not exercised")
	}
	// Preserve non-nil empty results: JSON [] and null are observably different.
	if baselineAppend(nil) == nil || candidateAppend(nil) == nil {
		t.Fatal("empty contract")
	}
}
func FuzzPairs(f *testing.F) {
	f.Add([]byte{})
	f.Add([]byte{0, 1, 255, 2, 0})
	f.Fuzz(func(t *testing.T, raw []byte) {
		if len(raw) > 256 {
			t.Skip()
		}
		values := make([]int, len(raw))
		for i, value := range raw {
			values[i] = int(value) - 128
		}
		checkPairs(t, values)
	})
}
