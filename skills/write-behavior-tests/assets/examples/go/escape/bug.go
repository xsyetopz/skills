//go:build bug

package escape

// The shipped bug: the trailing-backslash check was missing.
const trailingOK = true
