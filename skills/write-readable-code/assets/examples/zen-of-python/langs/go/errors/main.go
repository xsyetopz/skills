// Errors should never pass silently: wrap with %w so callers can still
// match the cause, and never turn a failure into a zero value.
package main

import (
	"errors"
	"fmt"
	"io/fs"
	"os"
	"strconv"
)

// readLimit returns the limit stored in path. Both failures are returned.
func readLimit(path string) (int, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return 0, fmt.Errorf("read limit: %w", err)
	}
	limit, err := strconv.Atoi(string(data))
	if err != nil {
		return 0, fmt.Errorf("parse limit in %s: %w", path, err)
	}
	return limit, nil
}

// readLimitSilent is the replaced version: every failure becomes 0.
func readLimitSilent(path string) int {
	data, _ := os.ReadFile(path)
	limit, _ := strconv.Atoi(string(data))
	return limit
}

func check(ok bool, message string) {
	if !ok {
		fmt.Println("FAIL", message)
		os.Exit(1)
	}
}

func main() {
	dir, err := os.MkdirTemp("", "limit")
	check(err == nil, "tempdir")
	defer os.RemoveAll(dir)
	good, bad := dir+"/good", dir+"/bad"
	check(os.WriteFile(good, []byte("42"), 0o600) == nil, "write good")
	check(os.WriteFile(bad, []byte("4x2"), 0o600) == nil, "write bad")

	limit, err := readLimit(good)
	check(err == nil && limit == 42, "good file")
	_, err = readLimit(dir + "/missing")
	check(errors.Is(err, fs.ErrNotExist), "missing file keeps fs.ErrNotExist")
	_, err = readLimit(bad)
	var numErr *strconv.NumError
	check(errors.As(err, &numErr), "bad number keeps *strconv.NumError")
	fmt.Println("bad file:", err)

	check(readLimitSilent(dir+"/missing") == 0, "silent version")
	check(readLimitSilent(bad) == 0, "silent version")
	fmt.Println("silent version returned 0 for both failures")
}
