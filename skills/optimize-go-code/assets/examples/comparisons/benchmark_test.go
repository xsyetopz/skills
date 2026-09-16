package main

import "testing"

var sinkInts []int
var sinkCounts map[string]int
var sinkBools []bool
var sinkString string
var sinkBytes []byte
var sinkSum int64

func BenchmarkAppend(b *testing.B) {
	values, _ := workload(2048)
	b.Run("baseline", func(b *testing.B) {
		b.ReportAllocs()
		for i := 0; i < b.N; i++ {
			sinkInts = baselineAppend(values)
		}
	})
	b.Run("candidate", func(b *testing.B) {
		b.ReportAllocs()
		for i := 0; i < b.N; i++ {
			sinkInts = candidateAppend(values)
		}
	})
}

func BenchmarkCounts(b *testing.B) {
	_, texts := workload(2048)
	b.Run("baseline", func(b *testing.B) {
		b.ReportAllocs()
		for i := 0; i < b.N; i++ {
			sinkCounts = baselineCounts(texts)
		}
	})
	b.Run("candidate", func(b *testing.B) {
		b.ReportAllocs()
		for i := 0; i < b.N; i++ {
			sinkCounts = candidateCounts(texts)
		}
	})
}

func BenchmarkMembership(b *testing.B) {
	_, texts := workload(2048)
	b.Run("baseline", func(b *testing.B) {
		b.ReportAllocs()
		for i := 0; i < b.N; i++ {
			sinkBools = baselineMembership(texts, texts)
		}
	})
	b.Run("candidate", func(b *testing.B) {
		b.ReportAllocs()
		for i := 0; i < b.N; i++ {
			sinkBools = candidateMembership(texts, texts)
		}
	})
}

func BenchmarkJoin(b *testing.B) {
	_, texts := workload(2048)
	b.Run("baseline", func(b *testing.B) {
		b.ReportAllocs()
		for i := 0; i < b.N; i++ {
			sinkString = baselineJoin(texts)
		}
	})
	b.Run("candidate", func(b *testing.B) {
		b.ReportAllocs()
		for i := 0; i < b.N; i++ {
			sinkString = candidateJoin(texts)
		}
	})
}

func BenchmarkFormat(b *testing.B) {
	values, _ := workload(2048)
	b.Run("baseline", func(b *testing.B) {
		b.ReportAllocs()
		for i := 0; i < b.N; i++ {
			sinkBytes = baselineFormat(values)
		}
	})
	b.Run("candidate", func(b *testing.B) {
		b.ReportAllocs()
		for i := 0; i < b.N; i++ {
			sinkBytes = candidateFormat(values)
		}
	})
}

func BenchmarkSum(b *testing.B) {
	values, _ := workload(2048)
	b.Run("baseline", func(b *testing.B) {
		b.ReportAllocs()
		for i := 0; i < b.N; i++ {
			sinkSum = baselineSum(values)
		}
	})
	b.Run("candidate", func(b *testing.B) {
		b.ReportAllocs()
		for i := 0; i < b.N; i++ {
			sinkSum = candidateSum(values)
		}
	})
}
