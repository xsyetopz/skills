package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"strconv"
	"strings"
)

func baselineAppend(values []int) []int {
	result := make([]int, 0)
	for _, value := range values {
		next := make([]int, len(result)+1)
		copy(next, result)
		next[len(result)] = value
		result = next
	}
	return result
}
func candidateAppend(values []int) []int {
	result := make([]int, 0, len(values))
	for _, value := range values {
		result = append(result, value)
	}
	return result
}
func baselineCounts(values []string) map[string]int {
	result := make(map[string]int)
	for _, value := range values {
		count := 0
		for _, other := range values {
			if value == other {
				count++
			}
		}
		result[value] = count
	}
	return result
}
func candidateCounts(values []string) map[string]int {
	result := make(map[string]int)
	for _, value := range values {
		result[value]++
	}
	return result
}
func baselineMembership(values, queries []string) []bool {
	result := make([]bool, len(queries))
	for i, query := range queries {
		for _, value := range values {
			if value == query {
				result[i] = true
				break
			}
		}
	}
	return result
}
func candidateMembership(values, queries []string) []bool {
	members := make(map[string]struct{}, len(values))
	for _, value := range values {
		members[value] = struct{}{}
	}
	result := make([]bool, len(queries))
	for i, query := range queries {
		_, result[i] = members[query]
	}
	return result
}
func baselineJoin(values []string) string {
	result := ""
	for _, value := range values {
		result += value
	}
	return result
}
func candidateJoin(values []string) string {
	var result strings.Builder
	for _, value := range values {
		result.WriteString(value)
	}
	return result.String()
}
func baselineFormat(values []int) []byte {
	result := make([]byte, 0)
	for i, value := range values {
		if i != 0 {
			result = append(result, ',')
		}
		result = append(result, fmt.Sprintf("%d", value)...)
	}
	return result
}
func candidateFormat(values []int) []byte {
	result := make([]byte, 0)
	for i, value := range values {
		if i != 0 {
			result = append(result, ',')
		}
		result = strconv.AppendInt(result, int64(value), 10)
	}
	return result
}
func baselineSum(values []int) int64 {
	selected := make([]int64, 0)
	for _, value := range values {
		if value%2 == 0 {
			selected = append(selected, int64(value))
		}
	}
	var sum int64
	for _, value := range selected {
		sum += value * value
	}
	return sum
}
func candidateSum(values []int) int64 {
	var sum int64
	for _, value := range values {
		if value%2 == 0 {
			sum += int64(value) * int64(value)
		}
	}
	return sum
}
func baselineInterfaceSum(values []int) int64 {
	boxed := make([]any, len(values))
	for i, value := range values {
		boxed[i] = value
	}
	var sum int64
	for _, value := range boxed {
		sum += int64(value.(int))
	}
	return sum
}
func candidateConcreteSum(values []int) int64 {
	var sum int64
	for _, value := range values {
		sum += int64(value)
	}
	return sum
}
func baselinePerItemChannels(values []int) []int {
	result := make([]int, len(values))
	channels := make([]chan int, len(values))
	for i, value := range values {
		channels[i] = make(chan int, 1)
		go func(index, item int) { channels[index] <- item }(i, value)
	}
	for i, channel := range channels {
		result[i] = <-channel
	}
	return result
}
func candidateBoundedBatch(values []int) []int {
	result := make([]int, 0, len(values))
	const batch = 32
	for start := 0; start < len(values); start += batch {
		end := start + batch
		if end > len(values) {
			end = len(values)
		}
		result = append(result, values[start:end]...)
	}
	return result
}
func baselineDistinct(values []int) []int {
	result := make([]int, 0)
	for _, value := range values {
		found := false
		for _, existing := range result {
			if existing == value {
				found = true
				break
			}
		}
		if !found {
			result = append(result, value)
		}
	}
	return result
}
func candidateDistinct(values []int) []int {
	seen := make(map[int]struct{}, len(values))
	result := make([]int, 0, len(values))
	for _, value := range values {
		if _, ok := seen[value]; !ok {
			seen[value] = struct{}{}
			result = append(result, value)
		}
	}
	return result
}
func baselineDelimiterCount(value string) int  { return len(strings.Split(value, ":")) - 1 }
func candidateDelimiterCount(value string) int { return strings.Count(value, ":") }
func baselineReverse(values []int) []int {
	result := make([]int, 0, len(values))
	for _, value := range values {
		result = append([]int{value}, result...)
	}
	return result
}
func candidateReverse(values []int) []int {
	result := make([]int, len(values))
	for i, value := range values {
		result[len(values)-1-i] = value
	}
	return result
}
func baselinePositiveSquares(values []int) []int64 {
	result := make([]int64, 0)
	for _, value := range values {
		if value > 0 {
			result = append(result, int64(value)*int64(value))
		}
	}
	return result
}
func candidatePositiveSquares(values []int) []int64 {
	result := make([]int64, 0, len(values))
	for _, value := range values {
		if value > 0 {
			result = append(result, int64(value)*int64(value))
		}
	}
	return result
}
func workload(size int) ([]int, []string) {
	values := make([]int, size)
	texts := make([]string, size)
	for i := range values {
		values[i] = i%31 - 15
		texts[i] = strconv.Itoa(values[i])
	}
	return values, texts
}
func run(args []string) error {
	if len(args) != 3 || (args[0] != "baseline" && args[0] != "candidate") {
		return errors.New("usage: pairs baseline|candidate CASE SIZE")
	}
	which, err := strconv.Atoi(args[1])
	if err != nil {
		return err
	}
	size, err := strconv.Atoi(args[2])
	if err != nil {
		return err
	}
	if size < 0 || size > 100000 {
		return errors.New("size must be 0..100000")
	}
	values, texts := workload(size)
	candidate := args[0] == "candidate"
	var result any
	switch which {
	case 1:
		if candidate {
			result = candidateAppend(values)
		} else {
			result = baselineAppend(values)
		}
	case 2:
		if candidate {
			result = candidateCounts(texts)
		} else {
			result = baselineCounts(texts)
		}
	case 3:
		if candidate {
			result = candidateMembership(texts, texts)
		} else {
			result = baselineMembership(texts, texts)
		}
	case 4:
		if candidate {
			result = candidateJoin(texts)
		} else {
			result = baselineJoin(texts)
		}
	case 5:
		if candidate {
			result = string(candidateFormat(values))
		} else {
			result = string(baselineFormat(values))
		}
	case 6:
		if candidate {
			result = candidateSum(values)
		} else {
			result = baselineSum(values)
		}
	case 7:
		if candidate {
			result = candidateConcreteSum(values)
		} else {
			result = baselineInterfaceSum(values)
		}
	case 8:
		if candidate {
			result = candidateBoundedBatch(values)
		} else {
			result = baselinePerItemChannels(values)
		}
	default:
		return errors.New("case must be 1..8")
	}
	return json.NewEncoder(os.Stdout).Encode(result)
}
func main() {
	if err := run(os.Args[1:]); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
